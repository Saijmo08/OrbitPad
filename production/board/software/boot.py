import board
import digitalio
import storage
import usb_cdc


try:
    import usb_midi
    usb_midi.disable()
except ImportError:
    pass

service = digitalio.DigitalInOut(board.GP15)
service.switch_to_input(pull=digitalio.Pull.UP)
maintenance = not service.value
service.deinit()  

usb_cdc.enable(console=True, data=True)


if not maintenance:
    storage.disable_usb_drive()
    
    storage.remount('/', readonly=False)

