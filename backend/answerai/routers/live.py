"""Provider-neutral live audio/video calls. Provider keys remain on the server."""

import asyncio
import base64
import binascii
import json
import logging
import os
import time
from typing import Literal
from uuid import uuid4

import aiohttp
import anyio
from answerai.internal.db import get_async_db
from answerai.models.billing import LiveLease
from answerai.models.config import Config
from answerai.routers.mfa import MfaRoute
from answerai.utils.auth import get_admin_user, get_verified_user, get_verified_user_by_token
from answerai.utils.plans import acquire_lease, entitlement, release_lease, require_feature, require_model, reserve
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import update

log = logging.getLogger(__name__)
router = APIRouter(route_class=MfaRoute)
GEMINI_URL = 'wss://generativelanguage.googleapis.com/ws/google.ai.generativelanguage.v1beta.GenerativeService.BidiGenerateContent'


class LiveSettings(BaseModel):
    model_config = ConfigDict(extra='forbid')
    enabled: bool = False
    openai_enabled: bool = True
    gemini_enabled: bool = True
    default_provider: Literal['openai', 'gemini'] = 'openai'
    openai_model: str = Field(default='gpt-realtime', min_length=1, max_length=200, pattern=r'^[a-zA-Z0-9._-]+$')
    openai_voice: str = Field(default='marin', min_length=1, max_length=100)
    gemini_model: str = Field(
        default='gemini-2.5-flash-native-audio-preview-12-2025',
        min_length=1,
        max_length=200,
        pattern=r'^[a-zA-Z0-9._-]+$',
    )
    gemini_voice: str = Field(default='Kore', min_length=1, max_length=100)
    camera_enabled: bool = True
    instructions: str = Field(
        default=(
            'You are ANSWERAI, a helpful voice assistant. Keep spoken replies concise. '
            'Describe camera content only when asked. You cannot execute tools or actions in this call.'
        ),
        max_length=10000,
    )


async def live_settings():
    return LiveSettings.model_validate(await Config.get('live.settings') or {})


def provider_key(provider):
    return os.getenv('OPENAI_REALTIME_API_KEY' if provider == 'openai' else 'GEMINI_LIVE_API_KEY', '')


def provider_model(config, provider):
    return getattr(config, provider + '_model')


@router.get('/config')
async def get_config(user=Depends(get_admin_user)):
    return {
        **(await live_settings()).model_dump(),
        'openai_key_configured': bool(provider_key('openai')),
        'gemini_key_configured': bool(provider_key('gemini')),
    }


@router.post('/config')
async def save_config(form: LiveSettings, user=Depends(get_admin_user)):
    await Config.upsert({'live.settings': form.model_dump(), 'audio.realtime.enabled': form.enabled})
    return await get_config(user)


@router.get('/providers')
async def providers(user=Depends(get_verified_user)):
    config = await live_settings()
    name, plan, billing = await entitlement(user)
    allowed = name == 'admin' or (name != 'blocked' and (not billing.enabled or plan.features.get('live_calls', False)))
    options = []
    if config.enabled:
        for provider in ('openai', 'gemini'):
            if getattr(config, provider + '_enabled') and provider_key(provider):
                model = provider_model(config, provider)
                model_allowed = (
                    name == 'admin'
                    or not billing.enabled
                    or '*' in plan.models
                    or f'live:{provider}/{model}' in plan.models
                )
                options.append(
                    {
                        'id': provider,
                        'name': 'OpenAI Realtime' if provider == 'openai' else 'Gemini Live',
                        'model': model,
                        'allowed': allowed and model_allowed,
                    }
                )
    return {
        'enabled': config.enabled,
        'providers': options,
        'default_provider': config.default_provider,
        'allowed': allowed,
        'camera_allowed': config.camera_enabled
        and (name == 'admin' or not billing.enabled or plan.features.get('live_video', False)),
        'max_call_minutes': plan.max_call_minutes,
    }


def decode_media(value, maximum, audio=False):
    if not isinstance(value, str) or len(value) > maximum * 4 // 3 + 4:
        raise ValueError('Media frame is too large.')
    try:
        raw = base64.b64decode(value, validate=True)
    except (ValueError, binascii.Error):
        raise ValueError('Invalid media encoding.') from None
    if not raw or len(raw) > maximum or (audio and len(raw) % 2):
        raise ValueError('Invalid media frame.')
    if not audio and not raw.startswith(b'\xff\xd8\xff'):
        raise ValueError('Camera frames must be JPEG images.')
    return raw


def provider_setup(config, provider):
    if provider == 'gemini':
        return {
            'setup': {
                'model': 'models/' + config.gemini_model,
                'generationConfig': {
                    'responseModalities': ['AUDIO'],
                    'speechConfig': {'voiceConfig': {'prebuiltVoiceConfig': {'voiceName': config.gemini_voice}}},
                },
                'systemInstruction': {'parts': [{'text': config.instructions}]},
                'inputAudioTranscription': {},
                'outputAudioTranscription': {},
                'realtimeInputConfig': {'automaticActivityDetection': {}},
                'contextWindowCompression': {'slidingWindow': {}},
            }
        }
    return {
        'type': 'session.update',
        'session': {
            'type': 'realtime',
            'instructions': config.instructions,
            'output_modalities': ['audio'],
            'audio': {
                'input': {
                    'format': {'type': 'audio/pcm', 'rate': 24000},
                    'transcription': {'model': 'gpt-4o-mini-transcribe'},
                    'turn_detection': {'type': 'server_vad', 'create_response': True, 'interrupt_response': True},
                },
                'output': {'format': {'type': 'audio/pcm', 'rate': 24000}, 'voice': config.openai_voice},
            },
        },
    }


def input_events(provider, message):
    kind = message.get('type')
    if kind == 'audio':
        decode_media(message.get('data'), 12000, audio=True)
        return (
            [{'type': 'input_audio_buffer.append', 'audio': message['data']}]
            if provider == 'openai'
            else [{'realtimeInput': {'audio': {'mimeType': 'audio/pcm;rate=16000', 'data': message['data']}}}]
        )
    if kind == 'video':
        decode_media(message.get('data'), 180000)
        return (
            [
                {
                    'type': 'conversation.item.create',
                    'item': {
                        'type': 'message',
                        'role': 'user',
                        'content': [{'type': 'input_image', 'image_url': 'data:image/jpeg;base64,' + message['data']}],
                    },
                }
            ]
            if provider == 'openai'
            else [{'realtimeInput': {'video': {'mimeType': 'image/jpeg', 'data': message['data']}}}]
        )
    if kind == 'mute':
        return (
            [{'type': 'input_audio_buffer.clear'}]
            if provider == 'openai'
            else [{'realtimeInput': {'audioStreamEnd': True}}]
        )
    if kind == 'interrupt':
        return (
            [{'type': 'response.cancel'}] if provider == 'openai' else []
        )  # Gemini handles interruption through server VAD.
    raise ValueError('Unsupported live event.')


def output_events(provider, event):  # noqa: C901 - explicit provider protocol and lifecycle handling
    if provider == 'openai':
        kind = event.get('type')
        if kind == 'session.updated':
            return [{'type': 'ready', 'input_rate': 24000}]
        if kind == 'response.output_audio.delta':
            return [{'type': 'audio', 'data': event['delta']}]
        if kind == 'response.output_audio_transcript.delta':
            return [{'type': 'transcript', 'role': 'assistant', 'text': event['delta']}]
        if kind == 'conversation.item.input_audio_transcription.completed':
            return [{'type': 'transcript', 'role': 'user', 'text': event.get('transcript', ''), 'final': True}]
        if kind == 'response.done':
            if event.get('response', {}).get('status') == 'failed':
                return [{'type': 'error', 'message': 'The voice provider could not complete this response.'}]
            return [{'type': 'turn_done'}]
        if kind == 'input_audio_buffer.speech_started':
            return [{'type': 'interrupted'}]
        if kind == 'error':
            # response.cancel on an already finished response is harmless.
            if event.get('error', {}).get('code') == 'response_cancel_not_active':
                return []
            return [{'type': 'error', 'message': 'Voice provider rejected the request. Check the provider settings.'}]
        return []
    if 'setupComplete' in event:
        return [{'type': 'ready', 'input_rate': 16000}]
    if event.get('error'):
        return [{'type': 'error', 'message': 'Gemini Live could not complete the call.'}]
    content = event.get('serverContent', {})
    result = []
    if content.get('interrupted'):
        result.append({'type': 'interrupted'})
    for part in content.get('modelTurn', {}).get('parts', []):
        inline = part.get('inlineData', {})
        if inline.get('mimeType', '').startswith('audio/pcm') and inline.get('data'):
            result.append({'type': 'audio', 'data': inline['data']})
    for key, role in [('inputTranscription', 'user'), ('outputTranscription', 'assistant')]:
        text = content.get(key, {}).get('text')
        if text:
            result.append({'type': 'transcript', 'role': role, 'text': text})
    if content.get('turnComplete'):
        result.append({'type': 'turn_done'})
    if event.get('goAway'):
        result.append({'type': 'error', 'message': 'The provider session is ending. Start a new call to continue.'})
    return result


@router.websocket('/call')
async def call(ws: WebSocket):  # noqa: C901 - explicit provider protocol and lifecycle handling
    await ws.accept()
    user = None
    lease_id = str(uuid4())
    leased = False
    tasks = []
    try:
        async with asyncio.timeout(10):
            initial = await ws.receive_text()
        if len(initial) > 8192:
            raise ValueError('Invalid authentication message.')
        auth = json.loads(initial)
        if not isinstance(auth, dict) or auth.get('type') != 'auth' or not isinstance(auth.get('token'), str):
            raise ValueError('Authentication required.')
        user = await get_verified_user_by_token(auth['token'], getattr(ws.app.state, 'redis', None))
        if not user:
            raise ValueError('Sign in to start a call.')
        config = await live_settings()
        provider = auth.get('provider', config.default_provider)
        if (
            provider not in ('openai', 'gemini')
            or not config.enabled
            or not getattr(config, provider + '_enabled')
            or not provider_key(provider)
        ):
            raise ValueError('This live provider is not configured.')
        await require_feature(user, 'live_calls')
        await require_model(user, f'live:{provider}/{provider_model(config, provider)}')
        from answerai.utils.access_control import has_permission

        if user.role != 'admin':
            if not await has_permission(user.id, 'chat.call', await Config.get('user.permissions') or {}):
                raise ValueError('Call permission denied.')
        _, plan, billing = await entitlement(user)
        await acquire_lease(user.id, lease_id)
        leased = True
        await reserve(user.id, [('call_starts', 60, 3, 1)])
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None, sock_connect=15)) as session:
            url = (
                'wss://api.openai.com/v1/realtime?model=' + config.openai_model if provider == 'openai' else GEMINI_URL
            )
            headers = (
                {'Authorization': 'Bearer ' + provider_key(provider)}
                if provider == 'openai'
                else {'x-goog-api-key': provider_key(provider)}
            )
            async with session.ws_connect(url, headers=headers, heartbeat=20, max_msg_size=1048576) as upstream:
                await upstream.send_json(provider_setup(config, provider))
                # Wait for provider confirmation before charging the first minute.
                async with asyncio.timeout(20):
                    while True:
                        event = await upstream.receive_json()
                        normalized = output_events(provider, event)
                        if any(item['type'] == 'error' for item in normalized):
                            raise ValueError('Provider setup failed. Check model, voice, and credentials.')
                        ready = next((item for item in normalized if item['type'] == 'ready'), None)
                        if ready:
                            break
                if billing.enabled and user.role != 'admin':
                    await reserve(user.id, [('live_minutes', 86400, plan.live_minutes_per_day, 1)])
                await ws.send_json(
                    {
                        **ready,
                        'provider': provider,
                        'model': provider_model(config, provider),
                        'max_seconds': plan.max_call_minutes * 60,
                    }
                )

                async def browser_to_provider():  # noqa: C901 - explicit provider protocol and lifecycle handling
                    audio_window, audio_bytes, last_video = time.monotonic(), 0, 0.0
                    muted = False
                    while True:
                        raw = await ws.receive_text()
                        if len(raw) > 250000:
                            raise ValueError('Live frame is too large.')
                        message = json.loads(raw)
                        if not isinstance(message, dict):
                            raise ValueError('Invalid live event.')
                        kind = message.get('type')
                        if kind == 'end':
                            return
                        if kind == 'ping':
                            await ws.send_json({'type': 'pong'})
                            continue
                        if kind == 'mute':
                            muted = True
                        if kind == 'unmute':
                            muted = False
                            continue
                        if kind == 'audio':
                            if muted:
                                continue
                            now = time.monotonic()
                            if now - audio_window >= 1:
                                audio_window, audio_bytes = now, 0
                            audio_bytes += len(message.get('data', ''))
                            if audio_bytes > (96000 if provider == 'openai' else 64000):
                                raise ValueError('Audio is arriving too quickly.')
                        if kind == 'video':
                            if not (await live_settings()).camera_enabled:
                                raise ValueError('Camera input is disabled.')
                            await require_feature(user, 'live_video')
                            now = time.monotonic()
                            if now - last_video < 0.8:
                                raise ValueError('Camera frames are arriving too quickly.')
                            last_video = now
                        for item in input_events(provider, message):
                            await upstream.send_json(item)

                async def provider_to_browser():
                    async for message in upstream:
                        if message.type in (aiohttp.WSMsgType.TEXT, aiohttp.WSMsgType.BINARY):
                            event = json.loads(message.data)
                            for item in output_events(provider, event):
                                await ws.send_json(item)
                                if item['type'] == 'error':
                                    return
                        elif message.type == aiohttp.WSMsgType.ERROR:
                            raise ValueError('Provider disconnected.')

                async def monitor():
                    nonlocal user
                    started, next_charge = time.monotonic(), time.monotonic() + 60
                    while True:
                        await asyncio.sleep(5)
                        current = await get_verified_user_by_token(auth['token'], getattr(ws.app.state, 'redis', None))
                        current_config = await live_settings()
                        if (
                            not current
                            or not current_config.enabled
                            or not getattr(current_config, provider + '_enabled')
                        ):
                            raise ValueError('Your session ended or calls were disabled.')
                        user = current
                        await require_feature(current, 'live_calls')
                        if current.role != 'admin' and not await has_permission(
                            current.id, 'chat.call', await Config.get('user.permissions') or {}
                        ):
                            raise ValueError('Call permission was revoked.')
                        await require_model(current, f'live:{provider}/{provider_model(config, provider)}')
                        _, current_plan, current_billing = await entitlement(current)
                        if time.monotonic() - started >= min(plan.max_call_minutes, current_plan.max_call_minutes) * 60:
                            raise ValueError('Call duration limit reached. Start a new call to continue.')
                        async with get_async_db() as db:
                            changed = await db.execute(
                                update(LiveLease)
                                .where(LiveLease.user_id == user.id, LiveLease.session_id == lease_id)
                                .values(expires_at=int(time.time()) + 90)
                            )
                            if not changed.rowcount:
                                raise ValueError('Call lease expired.')
                            await db.commit()
                        if time.monotonic() >= next_charge:
                            if current_billing.enabled and current.role != 'admin':
                                await reserve(
                                    current.id, [('live_minutes', 86400, current_plan.live_minutes_per_day, 1)]
                                )
                            next_charge += 60

                tasks = [asyncio.create_task(fn()) for fn in (browser_to_provider, provider_to_browser, monitor)]
                done, _ = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    task.result()
    except WebSocketDisconnect:
        pass
    except (HTTPException, ValueError) as exc:
        try:
            await ws.send_json({'type': 'error', 'message': exc.detail if isinstance(exc, HTTPException) else str(exc)})
        except Exception:
            pass
    except Exception:
        log.warning('Live call ended unexpectedly; provider credentials and media withheld.')
        try:
            await ws.send_json(
                {'type': 'error', 'message': 'Call connection failed. Check provider settings and try again.'}
            )
        except Exception:
            pass
    finally:
        # A disconnect can cancel the handler itself; still release media tasks and leases.
        with anyio.CancelScope(shield=True):
            for task in tasks:
                task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            if user and leased:
                async with asyncio.timeout(5):
                    await release_lease(user.id, lease_id)
            try:
                await ws.close()
            except Exception:
                pass
