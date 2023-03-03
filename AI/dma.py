from pynq import Overlay
from pynq import allocate
import numpy as np

NUM_OUTPUT = 1

def extract_features(input):

    return

def dma(input):

    # Line 13 and 14 (two lines below to be removed and add to main configuration/inital setup when starting script)
    ol = Overlay('design_1_wrapper.bit')
    dma = ol.axi_dma_0

    features = extract_features(input)

    run = True

    input_buffer = allocate(shape=(features.len(),), dtype=np.int16)
    output_buffer = allocate(shape=(NUM_OUTPUT,), dtype=np.int16)

    for i in range(features.len()):
        input_buffer[i] = features[i]

    print("Initial config:\n", dma.register_map)
    while run:
        try:
            dma.sendchannel.transfer(input_buffer)
            dma.recvchannel.transfer(output_buffer)
            dma.sendchannel.wait()
            dma.recvchannel.wait()

            action = output_buffer[0]

            if action == 1:
                return "logout"
            elif action == 2:
                return "shield"
            elif action == 3:
                return "reload"
            elif action == 4:
                return "grenade" 
            elif action == 5:
                return "none"
            
            run = False
        except RuntimeError as e:
            print(e)
            print("Error config: ", dma.register_map)


    # Call below statements once the buffers are no longer needed to free mem
    # del input_buffer
    # del output_buffer

        