import sys, datetime
sys.path.append('../')
import pypqlx
import matplotlib.pyplot as plt


def plot_average(periods, average_noise, w3_average_noise, w6_average_noise, network, station, begin, end):

    t, h = pypqlx.get_nhnm()
    t, l = pypqlx.get_nlnm()

    fig, ax = plt.subplots()
    ax.semilogx(t, h, color='tab:gray')
    ax.semilogx(t, l, color='tab:gray')

    ax.semilogx(periods, average_noise, color='tab:red', label='Average Noise')
    ax.semilogx(periods, w3_average_noise, color='tab:green', label='Last 3 weeks')
    ax.semilogx(periods, w6_average_noise, color='tab:blue', label='Last 6 weeks')
    ax.legend()
    ax.set_xlabel('Period [s]')
    ax.set_ylabel('Amplitude [$m^2/s^4/Hz$] [dB]')

    ax.grid()
    plt.xlim(0.1, 179)

    plt.title('%s %s Average Noise from %s to %s' % (network, station, begin, end))
    imgfile = ".".join((network, station, 'png'))
    plt.savefig(imgfile, dpi=100)
    print(imgfile,'generated.')
    plt.show()



#
## Main Code
#
if __name__ == "__main__":

    user     = ''
    password = ''
    machine  = ''
    basedb   = ''

    db = pypqlx.PQLXdb(user, password, machine, basedb)

    start = pypqlx.pdate(sys.argv[1])
    end   = pypqlx.pdate(sys.argv[2] + ' 23:59:00')
    net   = sys.argv[3]
    sta   = sys.argv[4]
    cha   = sys.argv[5]

    #
    ## get current noise data
    #
    current_pdf = db.PDF(start, end, net, sta, cha)

    #
    ## get noise data from past 3 weeks
    #
    t = datetime.timedelta(weeks=3)
    w3_pdf = db.PDF(start-t, end-t, net, sta, cha)

    #
    ## get noise data from past 6 weeks
    #
    t = datetime.timedelta(weeks=6)
    w6_pdf = db.PDF(start-t, end-t, net, sta, cha)

    db.close()

    pers = sorted(set(current_pdf.period))

    plot_average(periods=pers,
                 average_noise=current_pdf.average(),
                 w3_average_noise=w3_pdf.average(),
                 w6_average_noise=w6_pdf.average(),
                 network=net,
                 station=sta,
                 begin=start.date(),
                 end=end.date())

