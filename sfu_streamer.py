
from __future__ import annotations
import ssl
import asyncio
import pathlib
from concurrent.futures import TimeoutError

from janus_client import JanusClient
from janus_client.plugin_sfu import JanusSFUPlugin
from typing import TYPE_CHECKING, Type
if TYPE_CHECKING:
    from janus_client import JanusSession

import numpy as np 


async def subscribe(session: JanusSession):
    # Create plugin
    plugin_handle: JanusSFUPlugin = await session.create_plugin_handle(JanusSFUPlugin)

    room_id = 1 
    user_id = np.random.randint(1e15, 1e16, 1)[0]

    print(f'Connecting to Janus SFU session with ID {room_id} and joining as user with ID {user_id}')
    
    participants = await plugin_handle.list_participants(room_id, user_id)
    print("participants ", participants)

    await plugin_handle.destroy()

    plugin_handle: JanusSFUPlugin = await session.create_plugin_handle(JanusSFUPlugin)
    await plugin_handle.subscribe(room_id, user_id, str(participants[0]))

    await asyncio.sleep(60*60)

    # Destroy plugin
    await plugin_handle.destroy()

async def connect_janus_sfu(sfu_uri, ssl_context):
    # Start connection
    client = JanusClient(uri=sfu_uri)
    await client.connect(ssl=ssl_context)

    # Create session
    session = await client.create_session()

    await subscribe(session)

    # Destroy session
    await session.destroy()

    # Destroy connection
    # await adminClient.disconnect()
    await client.disconnect()
    # print("End of main")

async def main():
    sfu_uri = "wss://cowebxr.com:8989/janus"

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    localhost_pem = pathlib.Path(__file__).with_name("lt_limmengkiat_name_my.crt")

    # ssl_context.load_verify_locations(localhost_pem)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    run_sfu_capture = asyncio.create_task(connect_janus_sfu(sfu_uri, ssl_context))
    # run_analyser = asyncio.create_task(stream_analyser())
    await asyncio.gather(run_sfu_capture)


if __name__ == "__main__":
    asyncio.run(main())

