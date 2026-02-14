import clr
clr.AddReferenceToFileAndPath(r'C:\Users\AstroPC\Git\occultation-tools\gps-timing-analysis\lib\AdvLib.dll')
from Adv import AdvFile2

adv = AdvFile2(r'C:\Users\AstroPC\Documents\GPS_Timing\02_51_03Z.adv')

print('First 10 frames:')
print('Frame | ElapsedTicks | Time (ms) | Interval (ms)')
print('-' * 60)

for i in range(10):
    ticks = adv.MainIndex[i].ElapsedTicks
    ms = ticks / 10000.0
    
    if i > 0:
        prev_ticks = adv.MainIndex[i-1].ElapsedTicks
        interval = (ticks - prev_ticks) / 10000.0
        print('{0:5d} | {1:12d} | {2:9.2f} | {3:9.2f}'.format(i, ticks, ms, interval))
    else:
        print('{0:5d} | {1:12d} | {2:9.2f} |'.format(i, ticks, ms))

adv.Close()
