
from .plugin_base import JanusPlugin
import asyncio

from aiortc import RTCPeerConnection, RTCSessionDescription, VideoStreamTrack
from aiortc.contrib.media import MediaPlayer, MediaRecorder

pcs = set()

class JanusSFUPlugin(JanusPlugin):
    """Janus SFU plugin instance

    Implements API to interact with the SFU plugin.
    """

    name = "janus.plugin.sfu"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.joined_event = asyncio.Event()
        self.loop = asyncio.get_running_loop()

        self.users = dict()
        self.jsep_response = dict()

    def handle_async_response(self, response: dict):
        if response["janus"] == "event":
            print("Event response:", response)
            if "plugindata" in response:
                print('\n')
                print(response["plugindata"]["data"])
                if response["plugindata"]["data"]["success"] == True:
                    self.joined_event.set()
                try:
                    self.users = response["plugindata"]["data"]["response"]["users"]["1"]
                except:
                    pass
                # if reponse 
                # if response["plugindata"]["data"]["videoroom"] == "attached":
                #     # Subscriber attached
                #     self.joined_event.set()
                # elif response["plugindata"]["data"]["videoroom"] == "joined":
                #     # Participant joined (joined as publisher but may not publish)
        else:
            print("Unimplemented response handle:", response["janus"])
            print(response)
        # Handle JSEP. Could be answer or offer.
        if "jsep" in response:
            asyncio.create_task(self.sdp_processing(response["jsep"]))

    async def join(self, room_id: int, user_id: int) -> None:
        """Join a room
        """

        await self.send({
            "janus": "message",
            "body": {
                "kind": "join",
                "room_id": str(room_id),
                "user_id": str(user_id),
                "subscribe": {
                    'notifications': False, 
                    'data': False,
                    }
            }
        })
        await self.joined_event.wait()

    async def list_participants(self, room_id: int, user_id: int) -> list:
        """
        Get list of participants in room
        """

        response = await self.send({
            "janus": "message",
            "body": {
                "kind": "join",
                "room_id": str(room_id),
                "user_id": str(user_id),
                "subscribe": {
                    'notifications': False, 
                    'data': False,
                    }
            }
        })
        await self.joined_event.wait()
        return self.users

    async def send_data(self, results_data: dict) -> None:
        response = await self.send({
            "janus": "message",
            "body": {
                "kind": "data",
                "whom": None,
                "body": str(results_data)
            }
        })

    async def subscribe(self, room_id: int, user_id: int, client_id: str) -> None:
        """Join a room
        """

        pc = RTCPeerConnection()
        pcs.add(pc)

        self.recorder = MediaRecorder("input_video.mp4")
        self.recorder = MediaRecorder(f'images/{client_id}-%3d.png')
        # self.recorder = MediaRecorder("test.mp4", options={'-v': '0', '-vcodec"': 'mpeg4', '-f': 'udp://127.0.0.1:23000'})
        
        # -v 0 -vcodec mpeg4 -f mpegts udp://127.0.0.1:23000

        @pc.on("track")
        async def on_track(track):
            print("Track %s received" % track.kind)
            if track.kind == "video":
                self.recorder.addTrack(track)
            if track.kind == "audio":
                self.recorder.addTrack(track)

        await self.send({
            "janus": "message",
            "body": {
                "kind": "join",
                "room_id": str(room_id),
                "user_id": str(user_id),
                "subscribe": {
                    'notifications': False, 
                    'data': False,
                    'media': client_id
                    }
            },
        })

        self.pc = pc

    async def sdp_processing(self, jsep):
        # apply offer
        await self.pc.setRemoteDescription(
            RTCSessionDescription(
                sdp=jsep["sdp"], type=jsep["type"]
            )
        )
        await self.pc.setLocalDescription(await self.pc.createAnswer())
        payload = {
            "janus": "message",
            "body": {},
            "jsep": {
                    'sdp': self.pc.localDescription.sdp,
                    'type': self.pc.localDescription.type,
                    'trickle': True
                }
        }
        await self.send(payload)

        await self.recorder.start()
        await asyncio.sleep(60*60) # record for an hour
        await self.recorder.stop()
