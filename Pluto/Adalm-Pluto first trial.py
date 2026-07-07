import numpy as np
import adi
import matplotlib.pyplot as plt
import os
import pandas as pd
from scipy.signal import find_peaks

sample_rate = 6e6 # Hz
center_freq = 1420.405751766e6 # Hz
num_rows = int(1000) #observe 1000 times and average them
num_sub_samp = 1024 #number of samples per once
num_samps = int(num_sub_samp)*num_rows # number of samples per call to rx()

sdr = adi.Pluto("ip:192.168.2.1")
sdr.sample_rate = int(sample_rate)


# Config Rx (setting for Rxpin)
sdr.rx_lo = int(center_freq) # set what center frequency you want
sdr.rx_rf_bandwidth = int(sample_rate) # filter width, just set it to the same as sample rate for now
sdr.rx_buffer_size = num_sub_samp # how many samples you want
sdr.gain_control_mode_chan0 = 'manual'
sdr.rx_hardwaregain_chan0 = 50.0 # dB, increase to increase the receive gain, but be careful not to saturate the ADC

# Receive 1000 samples
data_list = []
for _ in range (num_rows):
    rx_samples = sdr.rx()
    psd_single = np.abs(np.fft.fftshift(np.fft.fft(rx_samples)))**2 
    # this codes are to perform a FFT to convert time into frequency data, rearrange the data horizontally so that the center of the graph is at 0Hz, and square the complex-valued data to calculate the power of radio wave (PSD).
    data_list.append(psd_single)
    
# Average 1000 detas    
psd_average = np.mean(data_list, axis=0)
psd_dB = 10*np.log10(psd_average) #transform the strength of radio to dB
f = np.linspace(sample_rate/-2, sample_rate/2, len(psd_dB)) # create a list of numbers to serve as the horizontal axis (frequency axis) of the graph


# Plot freq domain
plt.figure(0)
plt.title(f"Averaged frequency domain (Center :{center_freq/1e6:.3f} MHz)")
plt.plot((center_freq + f)/1e6, psd_dB)
plt.xlabel("Frequency [MHz]")
plt.ylabel("PSD [dB]") 
plt.show()

#Plot Spike freq
peaks, _ = find_peaks(psd_dB, height=90, distance = 100)

observed_freq = center_freq + f[peaks]

z=(center_freq-observed_freq)/observed_freq #equation for redshift/blueshift

c=299792458 #speed of light in m

wavelength=c/observed_freq

spike_data = { 'Spike_Frequency(Hz)' : observed_freq,
               'Spike_PSD(dB)' : psd_dB[peaks],
               'Status' :['redshift' if val>0 else 'blueshift' if val<0 else 'No shift' for val in z],
               'Wavelength(m)' : wavelength,
               'Recession Velocity(km/s)' : z*c/1000
             }

df_spikes = pd.DataFrame(spike_data)

output_file_path = 'Data_of_observed_hydrogen_line'

if df_spikes.empty:
    print("No radio spike detected")

else: 
    plt.figure(0)
    plt.title("Detected peak point of spikes of frequency")
    plt.plot((center_freq + f[peaks])/1e6, psd_dB[peaks], "o", markersize=8, label="Detected Peak")
    plt.xlabel("Frequency [MHz]")
    plt.ylabel("PSD [dB]") 
    plt.show()
    print(df_spikes)
    print()
    print(f"z = {z}")
    print()
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df_spikes.insert(0, 'Timestamp', current_time)
    file_exists = os.path.isfile(output_file_path)
    with open(output_file_path, 'a', newline='', encoding='utf-8') as csvfile:
        df_spikes.to_csv(csvfile, header=not file_exists, index=False)

    print(f"Data successfully saved to {output_file_path}")

print()
resolution=((sample_rate)/(num_sub_samp))/(center_freq)

print(f"The resolution in spectrum is {resolution}")