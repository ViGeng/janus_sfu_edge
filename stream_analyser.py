import glob, os

def main():
    results_folder = 'images'
    image_limit = 50
    while True:
        # check for image files in folder
        images = glob.glob(f'{results_folder}/*.png')
        images.sort(key=os.path.getmtime)

        total_num_images = len(images)
        print(total_num_images, images[-1])

        if total_num_images > image_limit:
            images_to_remove = images[:-image_limit]

            # remove images
            [os.remove(os.path.join(f)) for f in images_to_remove]


        # take latest image

        # perform YOLOv8

        # return results somehow?

main()