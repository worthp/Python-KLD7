import argparse
import time
from kld7.kld7 import KLD7

radar = KLD7()

def main(device):
    r = radar.init(device)
    print(f"radar init response[{r}]")

    if (r == KLD7.RESPONSE.OK):
        print(f"radar inited[{radar._inited}] with device[{radar._device}]")
    else:
        print(f"radar failed to init[{r}]")
        
    radar.getRadarParameters()

    print(f'radar._software_version {radar._software_version}]')
    print(f'radar._base_frequency[{radar._base_frequency}]')
    print(f'radar._maximum_speed[{radar._maximum_speed}]')
    print(f'radar._maximum_range[{radar._maximum_range}]')
    print(f'radar._threshold_offset[{radar._threshold_offset}]')
    print(f'radar._tracking_filter_type[{radar._tracking_filter_type}]')
    print(f'radar._vibration_suppression[{radar._vibration_suppression}]')
    print(f'radar._minimum_detection_distance[{radar._minimum_detection_distance}]')
    print(f'radar._maximum_detection_distance[{radar._maximum_detection_distance}]')
    print(f'radar._minimum_detection_angle[{radar._minimum_detection_angle}]')
    print(f'radar._maximum_detection_angle[{radar._maximum_detection_angle}]')
    print(f'radar._minimum_detection_speed[{radar._minimum_detection_speed}]')
    print(f'radar._maximum_detection_speed[{radar._maximum_detection_speed}]')
    print(f'radar._detection_direction[{radar._detection_direction}]')
    print(f'radar._range_threshold[{radar._range_threshold}]')
    print(f'radar._angle_threshold[{radar._angle_threshold}]')
    print(f'radar._speed_threshold[{radar._speed_threshold}]')
    print(f'radar._digital_output_1[{radar._digital_output_1}]')
    print(f'radar._digital_output_2[{radar._digital_output_2}]')
    print(f'radar._digital_output_3[{radar._digital_output_3}]')
    print(f'radar._hold_time[{radar._hold_time}]')
    print(f'radar._micro_detection_retrigger[{radar._micro_detection_retrigger}]')
    print(f'radar._micro_detection_sensitivity[{radar._micro_detection_sensitivity}]')
    
    r = radar.disconnect()
    print(f"radar disconnect response[{r}]")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--device", help="which device")
    args = parser.parse_args()
    main(args.device)