from bluepy.btle import Scanner, DefaultDelegate, Peripheral, UUID


# dev = Peripheral("D0:39:72:BF:C6:07")
dev = Peripheral("D0:39:72:BF:BF:BB")

try:
    ch = dev.getCharacteristics()
    # print(ch.read())
    for c in ch:
        print("c ", c)
        print("  0x" + format(ch.getHandle(), '02X') + "   " + str(ch.uuid) + " " + ch.propertiesToString())
finally:
    dev.disconnect()