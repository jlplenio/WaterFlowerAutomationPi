import time
from threading import Thread

import scrollphathd as phat
from scrollphathd.fonts import font5x5, font3x5

global finfo

finfo = {
    "temp": 99,
    "moist": 99,
    "condu": 99,
    "batt": 99,
    "light": 99,
}


def get_flower_data():
    from miflora.miflora_poller import MiFloraPoller, \
        MI_CONDUCTIVITY, MI_MOISTURE, MI_LIGHT, MI_TEMPERATURE, MI_BATTERY

    global finfo

    while True:
        poller = MiFloraPoller("C4:7C:8D:64:3F:F7")

        finfo = {
            "temp": poller.parameter_value("temperature"),
            "moist": poller.parameter_value(MI_MOISTURE),
            "condu": poller.parameter_value(MI_CONDUCTIVITY),
            "batt": poller.parameter_value(MI_BATTERY),
            "light": poller.parameter_value(MI_LIGHT),
        }

        log_to_csv(finfo)
        sleeptime = 900
        print(time.strftime("%d-%m-%y %H:%M"), "polling finished! - Sleeping {}min...".format(sleeptime / 60))
        time.sleep(sleeptime)


def log_to_csv(infodict):
    import csv, os.path
    from datetime import datetime

    file_exists = os.path.isfile('finfo.csv')

    i = datetime.now()
    infodict['date'] = i.strftime('%Y/%m/%d')
    infodict['time'] = i.strftime('%H:%M:%S')

    with open('finfo.csv', 'a', newline='') as csvfile:
        w = csv.DictWriter(csvfile, fieldnames=["date", "time", "temp", "moist", "condu", "batt", "light"],
                           delimiter=';')
        if not file_exists:
            w.writeheader()

        w.writerow(finfo)


def show_flower(waittime):
    phat.clear()
    brightness = 0.3

    global finfo

    phat.write_string(str(finfo['moist']), 0, 0, font5x5, 1, brightness)
    phat.write_string(str(finfo['temp'])[:2], 10, 0, font5x5, 1, brightness)
    bbattery = (finfo['batt'] % 100) / 99 * 17
    for x in range(17):
        if x < int(bbattery):
            phat.set_pixel(x, 6, brightness)
        else:
            phat.set_pixel(x, 6, brightness - 0.2)
    for y in range(1, 5):
        phat.set_pixel(8, y, brightness)

    phat.show()
    time.sleep(waittime)


def show_clock():
    # Display a progress bar for seconds
    # Displays a dot if False
    BRIGHTNESS = 0.3

    while int((time.time() % 60)) not in [20, 40]:
        phat.clear()
        float_sec = (time.time() % 60) / 59.0
        seconds_progress = float_sec * 15

        for y in range(15):
            current_pixel = min(seconds_progress, 1)
            phat.set_pixel(y + 1, 6, current_pixel * BRIGHTNESS)
            seconds_progress -= 1

            if seconds_progress <= 0:
                break
        phat.write_string(
            time.strftime("%H:%M"),
            x=0,  # Align to the left of the buffer
            y=0,  # Align to the top of the buffer
            font=font5x5,  # Use the font5x5 font we imported above
            brightness=BRIGHTNESS  # Use our global brightness value
        )

        if int(time.time()) % 2 == 0:
            phat.clear_rect(8, 0, 1, 5)

        phat.show()
        time.sleep(0.1)

def flower_water_checker():
    # pip3 install schedule
    checkattime = "21:00"
    moisturethreshold = 30
    waterhowlong = 5

    import schedule
    import time

    def check_moisture():
        global finfo
        moisture = finfo['moist']
        if moisture < moisturethreshold:
            print("Moisture {} is lower than threshold {}".format(moisture, moisturethreshold))
            water_for_x(waterhowlong)
        else:
            print("Moisture {} is higher than threshold {}".format(moisture, moisturethreshold))

    def water_for_x(sec):
        from os import system as system_call
        import time
        time.sleep(5)

        # todo Email an mich, dass es los geht mit sleep(300)


        for x in range(5):
            has_problem = system_call(
                "gatttool -b BB:A0:56:02:28:11 --char-write --handle 0x000f --value C5043132333435363738AA")
            if not has_problem:
                print("Successfully STARTED watering for {} seconds!".format(sec))
                break
            print("ERROR on try #{} to START watering for {} seconds!".format(x, sec))

        time.sleep(sec)

        for x in range(20):
            has_problem = system_call(
                "gatttool -b BB:A0:56:02:28:11 --char-write --handle 0x000f --value C5063132333435363738AA")
            if not has_problem:
                print("Successfully STOPPED watering for {} seconds!".format(sec))
                break
            print("ERROR on try #{} to STOP watering for {} seconds!".format(x, sec))

            #todo Email an mich wenn pumpe nicht gestoppt werden kann

    schedule.every().day.at(checkattime).do(check_moisture)

    while True:
        schedule.run_pending()
        time.sleep(30)

def main():
    Thread(target=get_flower_data).start()
    print("Starting in 5...")
    time.sleep(5)
    Thread(target=flower_water_checker).start()
    while True:
        show_clock()
        show_flower(5)


main()