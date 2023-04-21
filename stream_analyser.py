import glob, os
from ultralytics import YOLO
import json

import ssl
import asyncio

from janus_client import JanusClient
from janus_client.plugin_sfu import JanusSFUPlugin
from janus_client import JanusSession

import numpy as np

async def publish(session: JanusSession):
    results_folder = 'images'
    image_limit = 50

    model = YOLO("yolov8n.pt")
    model.to('cuda')

    # Create plugin
    plugin_handle: JanusSFUPlugin = await session.create_plugin_handle(JanusSFUPlugin)

    room_id = 1 
    user_id = np.random.randint(1e15, 1e16, 1)[0]

    print(f'Connecting to Janus SFU session with ID {room_id} and joining as user with ID {user_id}')
    
    plugin_handle: JanusSFUPlugin = await session.create_plugin_handle(JanusSFUPlugin)
    join_room = await plugin_handle.join(room_id, user_id)

    previous_client = 0
    previous_frame = 0
    while True:
        # check for image files in folder
        images = glob.glob(f'{results_folder}/*.png')
        images.sort(key=os.path.getmtime)

        total_num_images = len(images)

        if total_num_images > image_limit:
            images_to_remove = images[:-image_limit]

            # remove images
            [os.remove(os.path.join(f)) for f in images_to_remove]

        # take latest image
        latest_image = images[-1] 

        # select name and frame number of the image
        image_name = latest_image.split('/')[-1]
        in_split = image_name.split('-')

        client_id = in_split[0]
        frame_no = in_split[1].split('.')[0]

        if previous_client != client_id or previous_frame != frame_no:
            # perform YOLOv8
            results = model(latest_image) #, save=True)
            
            results_final = []
            for result in results:
                curr_res_boxes  = result.boxes

                curr_res_class  = curr_res_boxes.cls

                curr_res_names = []
                for class_name in curr_res_class:
                    curr_res_names.append(model.names[int(class_name)])
                
                curr_res_bb     = curr_res_boxes.xywhn
                curr_res_conf   = curr_res_boxes.conf

                curr_res = {
                    'classes': curr_res_class.tolist(),
                    'names': curr_res_names,
                    'bb': curr_res_bb.tolist(),
                    'conf': curr_res_conf.tolist()
                }

                result_struct = {
                    'client_id': client_id,
                    'frame_no': frame_no,
                    'results': curr_res
                }

                results_final.append(result_struct)

            # return results as JSON
            results_to_client = {
                "dataType": "results", 
                "data": results_final
            }

            results_json = json.dumps(results_to_client)
            print(results_json)

            # broadcast results to Janus SFU 
            send_data = await plugin_handle.send_data(results_json)

        previous_client = client_id
        previous_frame = frame_no

        # print("ahh", previous_client, client_id, previous_frame, frame_no)
    # print("ahh2")

    await asyncio.sleep(60*60)

    # Destroy plugin
    # await plugin_handle.destroy()

async def connect_janus_sfu(sfu_uri, ssl_context):
    # Start connection
    client = JanusClient(uri=sfu_uri)
    await client.connect(ssl=ssl_context)

    # Create session
    session = await client.create_session()

    await publish(session)

    # Destroy session
    await session.destroy()

    # Destroy connection
    # await adminClient.disconnect()
    await client.disconnect()
    # print("End of main")


async def main():
    sfu_uri = "wss://cowebxr.com:8989/janus"

    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    run_sfu_capture = asyncio.create_task(connect_janus_sfu(sfu_uri, ssl_context))
    await asyncio.gather(run_sfu_capture)

if __name__ == "__main__":
    asyncio.run(main())