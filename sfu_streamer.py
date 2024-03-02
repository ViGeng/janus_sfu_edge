
from __future__ import annotations

import asyncio
import ssl
from concurrent.futures import TimeoutError
from typing import TYPE_CHECKING

from random_username.generate import generate_username

from janus_client import JanusClient
from janus_client.plugin_sfu import JanusSFUPlugin

if TYPE_CHECKING:
    from janus_client import JanusSession

import logging

# 获取aiortc包的日志记录器
aiortc_logger = logging.getLogger('aiortc')
aiortc_logger.setLevel(logging.INFO)  # 设置日志级别为INFO或更高级别（如WARNING、ERROR、CRITICAL）

# 如果您想要同时关闭其他包的debug信息，可以设置根记录器的级别
root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)

import numpy as np

from utils import logger


async def subscribe(session: JanusSession):
    # Create plugin
    plugin_handle: JanusSFUPlugin = await session.create_plugin_handle(JanusSFUPlugin)

    room_id = 1 
    user_id = np.random.randint(1e15, 1e16, 1)[0]
    logger.info(f'Connecting to Janus SFU session with Room:{room_id} and joining as UserID {user_id}')
    
    participants = await plugin_handle.list_participants(room_id, user_id)
    while len(participants) == 0:
        logger.info(f"No participants in the room: {room_id}, sleep 5 seconds and retry")
        await asyncio.sleep(5)
        participants = await plugin_handle.list_participants(room_id, user_id)
    logger.info("More than 1 participant in the room, destroy the plugin and create a new one")
    logger.info(f"Participants in the room: {participants}")

    await plugin_handle.destroy()

    plugin_handle: JanusSFUPlugin = await session.create_plugin_handle(JanusSFUPlugin)
    logger.info(f"Subscribing to the room: {room_id} as user: {user_id} to the participant: {participants[0]}")
    await plugin_handle.subscribe(room_id, user_id, str(participants[0]))

    await asyncio.sleep(60*60)

    # Destroy plugin
    await plugin_handle.destroy()

async def connect_janus_sfu(sfu_uri, ssl_context):
    # Start connection
    client = JanusClient(uri=sfu_uri)
    logger.info("JanusClient created, start connection to Janus server")
    await client.connect(ssl=ssl_context)
    logger.info("Connected to Janus server")

    # Create session
    session = await client.create_session()
    logger.info(f"Session created: Session ID: {session.id}, subscribing to the session")

    await subscribe(session)

    # Destroy session
    await session.destroy()

    # Destroy connection
    # await adminClient.disconnect()
    await client.disconnect()
    # print("End of main")

async def main():
    sfu_uri = "wss://webxr.wgeng.site:8080/janus"
    logger.info("SFU URI: %s", sfu_uri)
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    # localhost_pem = pathlib.Path(__file__).with_name("sslkeys/localhost.crt")
    # ssl_context.load_verify_locations(localhost_pem)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE
    logger.info("ssl context created, start connecting to Janus SFU server...")

    logger.info("Create tasks for Janus SFU connection")
    run_sfu_capture = asyncio.create_task(connect_janus_sfu(sfu_uri, ssl_context))
    # run_analyser = asyncio.create_task(stream_analyser())
    await asyncio.gather(run_sfu_capture)
    


if __name__ == "__main__":
    asyncio.run(main())

