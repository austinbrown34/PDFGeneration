from plotly import __version__
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot

from plotly.graph_objs import Bar, Scatter, Figure, Layout

import plotly.plotly as py
# Generate the figure

trace = Bar(x=[1,2,3],y=[4,5,6])
data = [trace]
layout = Layout(title='My Plot')
fig = Figure(data=data,layout=layout)

# Save the figure as a png image:
py.image.save_as(fig, 'my_plot.png')
