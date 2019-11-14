import sys, datetime
sys.path.append('../')
import pypqlx
import matplotlib.pyplot as plt
from optparse import OptionParser

VERSION = '1.0'


def plot_average(periods, average_noise, w3_average_noise, w6_average_noise, network, station, begin, end, show=False):

    t, h = pypqlx.get_nhnm()
    t, l = pypqlx.get_nlnm()

    fig, ax = plt.subplots()
    ax.semilogx(t, h, color='tab:gray')
    ax.semilogx(t, l, color='tab:gray')

    ax.semilogx(periods, average_noise, color='#E91E63', label='Average Noise')

    if (len(w3_data) > 0):
        ax.semilogx(periods, w3_average_noise, color='#2196F3', label='Last 3 weeks')

    if (len(w6_data) > 0):
        ax.semilogx(periods, w6_average_noise, color='#00C853', label='Last 6 weeks')

    ax.legend()
    ax.set_xlabel('Period [s]')
    ax.set_ylabel('Amplitude [$m^2/s^4/Hz$] [dB]')

    ax.grid()
    plt.xlim(0.1, 179)

    plt.title('%s %s Average Noise from %s to %s' % (network, station, begin, end))
    imgfile = ".".join((network, station, 'png'))
    plt.savefig(imgfile, dpi=200)
    print(imgfile,'generated.')
    if show:
        plt.show()


def make_cmdline_parser():

    parser = OptionParser(usage="%prog [options] <-m mode> <-s source> <-d destination>", version=VERSION, add_help_option = True)

    parser.add_option("-u","--username", type="string", dest="user",
                      help="Database username", default=None)

    parser.add_option("-p","--password", type="string", dest="password",
                      help="Database username password", default=None)

    parser.add_option("-H","--hostname", type="string", dest="hostname",
                      help="PQLX host", default=None)

    parser.add_option("-d","--database", type="string", dest="basedb",
                      help="PQLX database name", default=None)

    parser.add_option("-s","--starttime", type="string", dest="start",
                      help="Start date to analyse PSDs: YYYY-MM-DD", default=None)

    parser.add_option("-e","--endtime", type="string", dest="end",
                      help="end date to analyse PSDs: YYYY-MM-DD", default=None)

    parser.add_option("-S","--nslc", type="string", dest="nslc",
                      help="Stream to analyse. Format: NET_STA_LOC_CHA", default=None)

    parser.add_option("-l","--list", type="string", dest="stalist",
                      help="Optional. Give a list of stations to analyse. Txt format: NET STA CHA LOC", default=None)

    parser.add_option("-v", "--view", action="store_true", dest="view",
                      help="Optional. If you want to view generated plots", default=False)

    return parser



#
## Main Code
#
if __name__ == "__main__":
    #
    ## Parse command line
    #
    parser = make_cmdline_parser()
    (options, args) = parser.parse_args()

    #
    ## Making sure all mandatory options appeared:
    #
    mandatories = ["user", "password", "hostname", "basedb", "start", "end"]
    for m in mandatories:
        if not options.__dict__[m]:
            print("\n### Mandatory option is missing! ###\n")
            parser.print_help()
            exit(-1)
    #
    ## Filling Vars:
    #
    user     = options.user
    password = options.password
    hostname = options.hostname
    basedb   = options.basedb
    start    = pypqlx.pdate(options.start)
    end      = pypqlx.pdate(options.end) + datetime.timedelta(days=1)
    nslc     = options.nslc
    stalist  = options.stalist
    view     = options.view
    streams  = []

    if (nslc == None and stalist == None):
        print("\n### ERROR: You need to give a stream to analyse or a list of streams (txt file) ###\n")
        exit(-1)

    if stalist:
        lines = open(stalist, 'r').readlines()
        for line in lines:
            stream = " ".join((line.split('_')))
            streams.append(stream.strip())
    else:
        stream = " ".join((nslc.split('_')))
        streams.append(stream)

    #
    ## Making plots:
    #
    db = pypqlx.PQLXdb(user, password, hostname, basedb)

    for stream in streams:
        net, sta, loc, cha = stream.split(' ')

        #
        ## get current noise data
        #
        pdf_data = []

        try:
            current_pdf = db.PDF(start, end, net, sta, cha, loc)
            pers        = sorted(set(current_pdf.period))
            pdf_data    = current_pdf.average()
        except:
            print("Chosen database does not contain information about %s. Skipping..." % sta)
            continue

        if (len(pdf_data) == 0):
            print("Nothing to plot for %s, no data found for the given time window. Skipping..." % sta)
            continue

        else:

            #
            ## get noise data from past 3 weeks
            #
            delta   = datetime.timedelta(weeks=3)
            w3_pdf  = db.PDF(start - delta, end - delta, net, sta, cha, loc)
            w3_data = w3_pdf.average()

            if (len(w3_data) == 0):
                print("Chosen database does not contain information about last 3 weeks of %s. Will not plot." % sta)

            #
            ## get noise data from past 6 weeks
            #
            t = datetime.timedelta(weeks=6)
            w6_pdf = db.PDF(start - t, end - t, net, sta, cha, loc)
            w6_data = w6_pdf.average()

            if (len(w6_data) == 0):
                print("Chosen database does not contain information about last 6 weeks of %s. Will not plot." % sta)

            #
            ## Plot data
            #
            plot_average(periods=pers,
                         average_noise=pdf_data,
                         w3_average_noise=w3_data,
                         w6_average_noise=w6_data,
                         network=net,
                         station=sta,
                         begin=start.date(),
                         end=end.date(),
                         show=view)

    db.close()









