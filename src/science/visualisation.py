import xarray as xr
import numpy as np
import matplotlib
import matplotlib.figure
import matplotlib.pyplot as plt

matplotlib.use('agg')

CONFIDENCE_INTERVAL=0.05

def plink(x: float, e: float=2/3) -> float:
	y = np.arctan( np.log(x) ) / (np.pi / 2)
	return np.power(1 + y, e)


def PRlink(x: float, e:float=3) -> float:
	y = np.arctan(np.log(x)) / (np.pi / 2)
	return np.sign(y) * np.power(np.abs(y), e)


def plot_probability(stats: xr.DataArray) -> tuple[
	matplotlib.figure.Figure,
    plt.Axes
]:
    """
    TODO Docstring
	"""
	
    # Compute probability lower/median/upper bounds for plotting  
    qstats = stats.\
	    quantile(
		    [0.5*CONFIDENCE_INTERVAL, 0.5, 1-0.5*CONFIDENCE_INTERVAL],
		    dim="sample_MCMC"
	    ).\
		assign_coords(
			quantile=['ql', 'be', 'qu']
        )

    mm     = 1. / 25.4
    ratio  = 16 / 11
    nrow   = 1
    ncol   = 1
    width  = 180*mm
    height = width / ncol / ratio * nrow

    colors = ["red","blue"]
    yticks = np.array([0,1e-12,1e-6,1e-3,1e-2,1/30,1/10,0.2,0.5,1] )
    yticklabelsL = ["0",r"$10^{-12}$",r"$10^{-6}$",r"$10^{-3}$",r"$10^{-2}$","1/30","1/10","1/5","1/2","1"]
    yticklabelsR = [r"$\infty$","","","1000","100","30","10","5","2","1"]


    fig = plt.figure( figsize = (width,height) )
    ax  = fig.add_subplot( nrow , ncol , 1 )
    for iqp,qp in enumerate([qstats.loc[:,:,"pF"],qstats.loc[:,:,"pC"]]):
        ax.plot( qp.time , plink(qp.loc["be",:]) , color = colors[iqp] )
        ax.fill_between( qp.time , plink(qp.loc["ql",:]) , plink(qp.loc["qu",:]) , color = colors[iqp] , alpha = 0.5 )
    ax.set_yticks(plink(yticks))
    ax.set_yticklabels(yticklabelsL)
    ax.set_ylabel("Probability")
    ax.set_ylim(plink([0,1]))

    axR = fig.add_subplot( nrow , ncol , 1 , sharex = ax , frameon = False )
    axR.yaxis.tick_right()
    axR.set_yticks(plink(yticks))
    axR.set_yticklabels(yticklabelsR)
    axR.yaxis.set_label_position( "right" )
    axR.set_ylabel( "Return period" , rotation = 270 )
    ax.set_ylim(plink([0,1]))
    # ax.set_title("Return period of a "+str(input.rl_val())+"°C-event at ["+str(round(rl_calc()[2],2))+"°N ; "+str(round(rl_calc()[3],2))+" °E]")

    plt.tight_layout()

    return fig, ax
