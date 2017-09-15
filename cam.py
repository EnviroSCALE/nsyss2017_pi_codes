import time
import picamera
import paho.mqtt.publish as pub
import traceback
import pyimgur


def publish_link_app(value, hostname =  "iot.eclipse.org", event = "photo", device_id="74da382afd91" ):
    try:
        topic = "iotBUET/" + device_id + "/" + event
        pub.single(topic, payload=value, hostname=hostname, port=1883)
        return True
    except:
        print ("error")
        traceback.print_exc()
        return False


def upload_image():
    PATH = "pictures/image.jpg"
    CLIENT_ID = "a4bcb5f77bbdb68"
    im = pyimgur.Imgur(CLIENT_ID)
    uploaded_image = im.upload_image(PATH, title="Uploaded with PyImgur")
    print(uploaded_image.link)
    return uploaded_image.link



def take_picture(pic_name='image.jpg', delay=0):
    #pic_location = '/home/pi/workshop/camera/'
    pic_name = 'image.jpg'
    pic_location = 'pictures/'
    pic_location = pic_location + pic_name
    with picamera.PiCamera() as camera:
        camera.start_preview()
        time.sleep(delay)
        camera.capture(pic_location)
        camera.stop_preview()

    publish_link_app(upload_image())

#take_picture()









