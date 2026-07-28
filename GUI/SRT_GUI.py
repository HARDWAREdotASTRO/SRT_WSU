import dash
import dash_daq as daq
from dash.dependencies import Input, Output, State
from dash import dcc, html
from astropy.coordinates import EarthLocation
from astropy import units as u
from astropy import units as u
from astropy.coordinates import SkyCoord
from astropy.coordinates import AltAz
from astropy.coordinates import get_body
from astropy.time import Time
from astropy.table import Table
from datetime import datetime

import time
import serial
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objs as go

from IPython.display import Image
from astropy.visualization import astropy_mpl_style
plt.style.use(astropy_mpl_style)

#Initialize serial communication, this is often commented out to see the webpage when the Arduino is not hooked up

#ser1 = serial.Serial('/dev/serial/by-id/usb-Arduino__www.arduino.cc__0043_85438333835351901141-if00', baudrate = 9600, timeout=1) #tried to impliment serial connection via arduino ID
#ser2 = serial.Serial('/dev/serial/by-id/ usb-Arduino__www.arduino.cc__0043_75131313632351F081F1-if00', baudrate = 9600, timeout=1)

#ser1 = serial.Serial('/dev/ttyACM0', baudrate = 9600, timeout=1)
#ser2 = serial.Serial('/dev/ttyACM1', baudrate = 9600, timeout=1)


#Dummy variables for keeping track of button presses.
prevclick = 0
homeprev = 0
zeroprev = 0
altforprev = 0
altrevprev = 0
azforprev = 0
azrevprev = 0
delay1 = 0
#Blank string to be updated for updating the realtime location of the gear/dish
motAz = ""
motAlt = ""

# This is a list of commands in a seperate file online that my program would 
# automatically pull commands from. It will hopefully be replaced with
# one I'm having a comp sci guy produce.
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# This is to shorten the command needed to reference the CSS file as well as the Dash libraries
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# This is where the darkness begins.   
app.layout = html.Div([
    #Start with the banner at the top of the page
    html.Div(
        id="container",
        style={
            "backgroundColor": "#3f0099",
            "color": "white",
            "position": "relative",
            "padding": "10px",
            "height": "100px"},
        children=[
            html.H3("Winona State Small Radio Telescope Control"),

            html.A(
                html.Img(
                    src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSPlyNBjmPB7znjvxXWwSnz4wzOi61_nE1HGQ5ftisXgJ13XUNUyBlou6av&s=10%22",

                    style={
                        "height": "90px",
                        "position": "absolute",
                        "top": "10px",
                        "right": "10px"
                }
            ),
            href="https://www.winona.edu/",
            target="_blank"
            ),
            html.A(
                html.Img(
                    src="https://static.freepnglogo.com/images/all_img/github-logo-white-stroke-2a6c.png",

                    style={
                        "height": "90px",
                        "position": "absolute",
                        "top": "10px",
                        "right": "95px"
                }
            ),
            href="https://github.com/HARDWAREdotASTRO/SRT_WSU",
            target="_blank"
        ),
        html.Div([ #This shows the live date and time under the title
            html.Div(id='live-date-time'), 
            dcc.Interval(id='interval-component', interval=1000, n_intervals=0) # Updates every 1000ms
            ])
        ]
    ),
    
    html.Div([ #Status monitor to show/list important and relative information
            dcc.Textarea(
                id="status-monitor",
                placeholder=" ",
                value="",
                style={
                    "width": "99.75%",
                    "height": "75px",
                    "marginLeft": "0.25%",
                    "marginBottom": "0%",
                    },
                ),
            ],
                className="twelve columns",
                style={
                    "marginTop": "1%"
                }
            ),
    #Setup for the graph to display objects seen from Earth
    html.Div([
        #Dropdown bar to choose which planet will be selected
        html.Div([
            dcc.Dropdown(
                #ID for callback function
                id='solarsystem',
                #Dropdown selection options
                options=[
                    {'label': 'Object', 'value': 'object'},
                    {'label': 'Sun', 'value': 'sun'},
                    {'label': 'Moon', 'value': 'moon'},
                    {'label': 'Mercury', 'value': 'mercury'},
                    {'label': 'Venus', 'value': 'venus'},
                    {'label': 'Mars', 'value': 'mars'},
                    {'label': 'Jupiter', 'value': 'jupiter'},
                    {'label': 'Saturn', 'value': 'saturn'},
                    {'label': 'Uranus', 'value': 'uranus'},
                    {'label': 'Neptune', 'value': 'neptune'},
                ],
                #initial value
                value='sun'
            )
        ]
        ),
        #Initialize graph and id for callback
        html.Div([
            dcc.Graph(
                id='graph'
            )
        ],
            className="twelve columns",
            style={
                "marginTop": "3%"
            }
        )
    ],
        #Take up the full width of the page
        className='twelve columns'
    ),


    #Seperate the rest of the page
    html.Div([
        #Direct control compartment of the page
        html.Div([
                html.Div([
                    #Title
                    html.H3(
                        "Direct Control")
                ], 
                    className='Title'
                ),
            #Two buttons per row
                html.Div([
                     daq.StopButton(
                            id="stop-button", 
                            buttonText="STOP", #Button STOPS motors
                            style={
                                #Not entirely sure how these work, padding helpes seperate boxes, maybe
                                "display": "center",
                                "justify-content": "space-around",
                                "padding": "10px 10px 10px 10px"
                            },
                             #Six columns = half the row
                            className="six columns",
                            n_clicks=0
                        ),
                    daq.StopButton(
                            id="go-home-button",
                            buttonText="HOME", #Button makes telescope go HOME
                            style={
                                "display": "flex-right",
                                "justify-content": "space-around",
                                "padding": "10px 10px 10px 10px"
                            },
                            className="six columns",
                            n_clicks=0
                        ),
                   
                ],
                    style={
                        #Box shadow gives a light border
                        "align-items": "center",
                        'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                        "padding": "10px 10px 10px 20px"
                    },
                    #Take up the whole row
                    className="row"
                ),
                html.Div([
                    daq.StopButton(
                                id="zero-button",
                                buttonText="Zero", #Button will ZERO the SRT
                                style={
                                    "display": "flex-right",
                                    "justify-content": "space-around",
                                    "padding": "10px 10px 10px 10px"
                                },
                                className="six-columns",
                                n_clicks=0
                              )  
                ],
                    style={
                        #Box shadow gives a light border
                        "align-items": "center",
                        'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                        "padding": "10px 10px 10px 20px"
                    },
                    #Take up the whole row
                    className="row"
                ),    
            #Seperate the motor controls for each motor
                html.Div([
                    html.Div([
                        html.H5(
                            "Altitude Motor" #Altitude motor control
                        )
                    ], 
                        className='Title'
                    ),
                    html.Div([
                        html.Button(
                            "Forward",
                            id="alt-forward-button",
                            n_clicks=0,
                            className="three columns",
                            style={
                                "display": "flex",
                                "justifyContent": "space-around",
                                "alignItems": "center",
                                "padding": "10px",
                                "width": "45%",
                                "backgroundColor": "#4B08A1",
                                "color": "white",
                                "border": "1px solid #4B08A1",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontWeight": "600"
                            }
                        ),
                        
                        html.Button(
                            "Reverse",
                            id="alt-reverse-button",
                            n_clicks=0,
                            className="three columns",
                            style={
                                "display": "flex",
                                "justifyContent": "space-around",
                                "alignItems": "center",
                                "padding": "10px",
                                "width": "45%",
                                "backgroundColor": "#4B08A1",
                                "color": "white",
                                "border": "1px solid #4B08A1",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontWeight": "600"
                            }
                        )
                    ],
                        className="row"
                    ),
                    html.Div([
                        #A slider to control the motor speed
                        dcc.Slider(
                            id="alt-slider",
                            min=0,
                            max=100,
                            value=100
                        ),
                        html.Div(
                            id='speed-control-alt')
                        
                    ],
                        style={
                        "padding": "10px 10px 10px 20px"
                    },
                        className="row"
                    )
                ],
                    style={
                        "align-items": "center",
                        'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                        "padding": "10px 10px 10px 20px"
                    },
                        className="row"
                ),
                html.Div([
                    html.Div([
                        html.H5(
                            "Azimuth Motor" #Azimuth motor control
                        )
                    ], 
                        className='Title'
                    ),
                    html.Div([
                        html.Button(
                            "Forward",
                            id="az-forward-button",
                            n_clicks=0,
                            className="three columns",
                            style={
                                "display": "flex",
                                "justifyContent": "space-around",
                                "alignItems": "center",
                                "padding": "10px",
                                "width": "45%",
                                "backgroundColor": "#4B08A1",
                                "color": "white",
                                "border": "1px solid #4B08A1",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontWeight": "600"
                            }
                        ),
                        
                        html.Button(
                            "Reverse",
                            id="az-reverse-button",
                            n_clicks=0,
                            className="three columns",
                            style={
                                "display": "flex",
                                "justifyContent": "space-around",
                                "alignItems": "center",
                                "padding": "10px",
                                "width": "45%",
                                "backgroundColor": "#4B08A1",
                                "color": "white",
                                "border": "1px solid #4B08A1",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontWeight": "600"
                            }
                        )
                    ],
                        className="row"
                    ),
                    html.Div([
                        dcc.Slider(
                            id="az-slider", #Azimuth speed slider
                            min=0,
                            max=100,
                            value=100
                        ),
                        html.Div(
                            id='speed-control-az')
                        
                    ],
                        style={
                        "padding": "10px 10px 10px 20px"
                    },
                        className="row"
                    )
                ],
                    style={
                        "align-items": "center",
                        'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                        "padding": "10px 10px 10px 20px"
                    },
                        className="row"
                ),            
                
            ],
                style={
                    "align-items": "center",
                    "border": "1px solid #2a3f5f",
                    "border-radius": "4px",
                    #'boxShadow': '0px 0px 5px 5px rgba(204,204,204,0.4)',
                    "padding": "10px 10px 10px 20px"
                },
                #Direct control box takes a third of the page
                className="four columns"
            ),
            

            html.Div([
                #A box to callback the srt's current direction
                html.Div([
                    html.Div([
                        html.H3(
                            "SRT Direction"
                        )
                    ], 
                        className='Title'
                    ),
                    html.Div([
                        html.Div([
                            html.Div([
                                "Altitude:  " #updates as SRT moves in altitude 
                            ],
                                style={
                                    'textAlign': 'right'
                                },
                                className="three columns"
                            ),
                            html.Div(
                                id="altitude",
                                className="three columns",
                                style={
                                    'marginRight': '20px'
                                }
                            )
                        ], 
                            className="twelve columns"
                        ),
                        html.Div([
                            html.Div([
                                "Azimuth:  " #updates when SRT moves in the azimuth direction
                            ],
                                style={
                                    'textAlign': 'right'
                                },
                                className="three columns"
                            ),
                            html.Div(
                                id="azimuth",
                                className="three columns",
                                style={
                                    'marginRight': '20px'
                                }
                            )
                        ], 
                            className="twelve columns"
                        )
                    ],
                        style={
                            "align-items": "center",
                            'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                            "padding": "10px 10px 10px 20px"
                        },
                        className="twelve columns"
                    )
                ],
                    #Gets half the row, shares with Input direction
                    className="six columns"
                ),
                html.Div([
                    html.Div([
                        html.H3(
                            "Input Direction" #direction the user wants SRT to go
                        )
                    ], 
                        className='Title'
                    ),
                    html.Div([
                        #Reports alt az of ra and dec user input
                        html.Div([
                            html.Div([
                                "Altitude:  "
                            ],
                                style={
                                    'textAlign': 'right'
                                },
                                className="three columns"
                            ),
                            html.Div(
                                id="alt",
                                className="three columns",
                                style={
                                    'marginRight': '20px'
                                }
                            )
                        ], 
                            className="twelve columns"
                        ),
                        html.Div([
                            html.Div(
                                "Azimuth:   ",
                                style={
                                    'textAlign': 'right'
                                },
                                className="three columns"
                            ),
                            html.Div(
                                id="az",
                                className="four columns",
                                style={
                                    'marginRight': '20px'
                                }
                            )
                        ], 
                            className="twelve columns"
                        )
                    ],
                        style={
                            "align-items": "center",
                            'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                            "padding": "10px 10px 10px 20px"
                        },
                        className="twelve columns"
                    )
                ],
                    className="six columns"
                )                    
            ],
                style={
                    "align-items": "center",
                    "border": "1px solid #2a3f5f",
                    "border-radius": "4px",
                    'boxShadow': '0px 0px 5px 5px rgba(204,204,204,0.4)',
                    "padding": "20px 20px 20px 20px",
                    "MarginBottom": "2%"
                },
                className="eight columns",
        
            ),
            html.Div([
                #User input object
                html.Div([
                        html.H3(
                            "Object"
                        )
                ], 
                    className='Title'
                ),
                html.Div([
                    dcc.Input(
                        id='RA', 
                        value='24d20m30s', 
                        type='text',
                        className="ten columns"
                    ),
                    html.H5(
                        "Right Ascension", 
                        style={
                            "textAlign": "bottom"
                        }
                    )
                ], 
                    style={
                        "align-items": "center",
                        'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                        "padding": "10px 10px 10px 20px"
                    },
                    className='five columns'
                ),

                html.Div([
                    dcc.Input(
                        id='DEC', 
                        value='12d24m35s', 
                        type='text',
                        className="ten columns"
                    ),
                    html.H5(
                        "Declination", 
                        style={
                            "textAlign": "bottom"
                        }
                    )
                ],
                    style={
                        "align-items": "center",
                        'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                        "padding": "10px 10px 10px 20px"
                    },
                    className='five columns'
                ),
                html.Div([
                    html.Button(
                            "Go",
                            id="go-button",
                            n_clicks=0,
                            className="three columns",
                            style={
                                "display": "flex",
                                "justifyContent": "space-around",
                                "alignItems": "center",
                                "padding": "10px",
                                "width": "20%",
                                "backgroundColor": "#03AF4B",
                                "color": "white",
                                "border": "1px solid #056D30",
                                "borderRadius": "5px",
                                "cursor": "pointer",
                                "fontWeight": "600"
                            }
                        )
                ],                
                    style={
                        "align-items": "center",
                        "padding": "10px 10px 10px 20px"
                    },
                    className="twelve columns"
                ),
                
            ],
                style={
                    "align-items": "center",
                    "border": "1px solid #2a3f5f",
                    "border-radius": "4px",
                    "position": "relative",
                    "marginTop": "2%",
                    "marginBottom": "2%",
                    "padding": "10px 10px 10px 10px",
                    },
                className="eight columns"
            ),
            
            html.Div([
                    #Select how to observe
                    html.Div([
                            html.H3(
                                "Observing Method"
                            )
                        ], 
                            className='Title'
                        ),
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Method Select"
                                )
                            ], 
                                className='Title'
                                
                            ),
                            
                            #Pick the method
                            dcc.RadioItems(
                                id="select",
                                options=[
                                    {'label': 'Go To', 'value': 'Goto'},
                                    {'label': 'Tracking', 'value': 'Track'},
                                    {'label': 'Scan', 'value': 'Scan'}
                                ],
                                value='Goto'
                            ),
                        ],
                            style={
                                "align-items": "center",
                                'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                                "padding": "10px 10px 5px 10px"
                            },
                            className="twelve columns"
                        ),
                    html.Div([
                        #Boxes for specific method instructions
                        html.Div([
                            html.Div([
                                html.Div([
                                    html.H6(
                                        "Scan"
                                    )
                                ], 
                                    className='Title'
                                ),
                                dcc.RadioItems(
                                    id='scanner',
                                    options=[
                                        {'label': 'Full Sky', 'value': 'FullSky'},
                                        {'label': 'Object', 'value': 'Obj'}
                                    ],
                                    value='Obj'
                                )
                            ],
                                className="four columns"
                            ),
                            html.Div([
                                html.Div([
                                    html.H6(
                                        "Box Size"
                                    )
                                ], 
                                    className='Title',
                                    style={
                                    "marginLeft": "-30px"
                                    }
                                ),
                                html.Div([
                                    dcc.Input(
                                        id='boxSize', 
                                        value='10', 
                                        type='text',
                                        className="five columns",
                                        style={
                                            "marginLeft": "-30px"
                                        }
                                    ),
                                    html.H5(
                                        "°", 
                                        style={
                                            "paddingRight": "70%",
                                            "textAlign": "right"
                                        }
                                    )
                                ]
                                ) 
                        ],
                            className="four columns"
                        ),
                        html.Div([
                            html.Div([
                                html.H6(
                                    "Scan Speed"
                                )
                            ], 
                                className='Title',
                                style={
                                    "marginLeft": "-30px"
                                    }
                            ),
                            html.Div([
                                dcc.Input(
                                    id='scanSpeed', 
                                    value='10', 
                                    type='text',
                                    className="five columns",
                                    style={
                                        "marginLeft": "-30px"
                                    }
                                ),
                                html.H5(
                                    "°/min", 
                                    style={
                                        "paddingRight": "45%",
                                        "textAlign": "right"
                                    }
                                )
                            ], 
                                className='row'
                            )
                    ],
                        className="four columns"
                    ),
                    html.Div([
                        html.Div([
                            html.H6(
                                "Frequency Start"
                                )
                            ], 
                                className='Title',
                                    style={
                                    "marginLeft": "-30px"
                                    }
                            ),
                            html.Div([
                                dcc.Input(
                                    id='frequencyStart', 
                                    value='1420', 
                                    type='text',
                                    className="five columns",
                                        style={
                                            "marginLeft": "-30px"
                                        }
                                ),
                                html.H5(
                                    "MHz", 
                                    style={
                                        "paddingRight": "50%",
                                        "textAlign": "right"
                                    }
                                )
                            ], 
                                className='row'
                            )
                    ],
                        className="five columns"
                    ),
                    html.Div([
                        html.Div([
                            html.H6(
                                    "End"
                                    )
                                ], 
                                className='Title',
                                style={
                                    "marginTop": "-85px",
                                    "marginLeft": "325px"
                                    }
                        ),
                        html.Div([
                            dcc.Input(
                                id='frequencyEnd', 
                                value='1420.8', 
                                type='text',
                                className="five columns",
                                style={
                                    "marginTop": "0px",
                                    "marginLeft": "325px"
                                    }
                        ),
                            html.H5(
                                    "MHz", 
                                    style={
                                        "textAlign": "right",
                                        "marginRight": "-245px"
                                        }
                                    )
                                ], 
                                className='row'
                                )
                            ],
                            className="five columns"
                        )
                    ],
                        style={
                            "align-items": "center",
                            'boxShadow': '1px 1px 1px 1px rgba(204,204,204,0.4)',
                            "padding": "10px 10px 10px 10px"
                        },
                        className="row"
                    )
                    ]
                    ),
                ],
                    style={
                        "align-items": "center",
                        "border": "1px solid #2a3f5f",
                        "border-radius": "4px",
                        "padding": "10px 10px 10px 10px"
                        },
                    className="eight columns"
                ),

    
            html.Div([
                html.Div(id='go-home-button-count'),
                html.Div(id='stop-button-count'),
                html.Div(id='zero-button-count'),
                html.Div(id='alt-for-button-count'),
                html.Div(id='alt-rev-button-count'),
                html.Div(id='az-for-button-count'),
                html.Div(id='az-rev-button-count'),
                html.Div(id='placeholder'),
                dcc.RadioItems(
                    id='placeholder2',
                    options=[
                        {'label': 'Place', 
                         'value': 'Place'}
                    ],
                    value='Place'
                ),
                dcc.Interval(
                    id='refresher',
                    interval=1000),
                dcc.Interval(
                    id='refresher2',
                    interval=1000),
                
                dcc.Interval(
                    id='refresher3',
                    interval=10000)
            ],
                style={
                    "visibility": "hidden"
                }
            )
    ],
        className="row"
    ),
        html.Div(
            id="data-box",
            children=[
                html.H3(
                    "Data Settings",
                    style={
                        "position": "absolute",
                        "top": "5px",
                        "left": "10px",
                        "margin": "0px",
                    }
                ),
                html.Div(
                    [
                    daq.StopButton(
                        id="load-button",
                        buttonText="LOAD",
                        n_clicks=0,
                        style={
                            "margin": "5px",
                            "display": "flex",
                            "justify-content": "space-around",
                            "align-items": "center",
                            "position": "absolute",
                            "bottom": "10px",
                            "left": "-100px",
                            "right": "10px",
                            "top": "-50px"
                            },
                        ),
                    daq.StopButton(
                        id="save-button",
                        buttonText="SAVE",
                        n_clicks=0,
                        style={
                            "margin": "5px",
                            "display": "flex",
                            "justify-content": "space-around",
                            "align-items": "center",
                            "position": "absolute",
                            "bottom": "10px",
                            "left": "125px",
                            "right": "10px",
                            "top": "-50px"
                            },
                        ),
                        daq.StopButton(
                        id="reset-button",
                        buttonText="RESET",
                        n_clicks=0,
                        style={
                            "margin": "5px",
                            "display": "flex",
                            "justify-content": "space-around",
                            "align-items": "center",
                            "position": "absolute",
                            "bottom": "10px",
                            "left": "125px",
                            "right": "10px",
                            "top": "75px"
                            },
                        ),
                        daq.StopButton(
                        id="export-button",
                        buttonText="EXPORT",
                        n_clicks=0,
                        style={
                            "margin": "5px",
                            "display": "flex",
                            "justify-content": "space-around",
                            "align-items": "center",
                            "position": "absolute",
                            "bottom": "10px",
                            "left": "-100px",
                            "right": "10px",
                            "top": "75px"
                            },
                        ),
                    ],
                    
                ),
            ],
            style={
                "border": "1px solid black",
                "height": "225px",
                "width": "28%",
                "padding": "10px",
                "marginTop": "-250px",
                "marginBottom": "3%",
                "position": "relative",
            },
        ),
        html.Div([
            dcc.Graph(id='live-hydrogen-graph'),
            dcc.Interval(
                id='interval-component1',
                 interval=1*1000, # Update every 1000 milliseconds (1 second)
                n_intervals=0
                )
            ],
            className='twelve columns'
        ),
        html.Div(
        id="containerbottom",
        style={
            "backgroundColor": "#3f0099",
            "color": "white",
            "position": "relative",
            "padding": "10px",
            "top": "450px",
            "height": "100px"
            },
        children=[
            html.A(
                html.Img(
                    src="https://upload.wikimedia.org/wikipedia/en/c/cb/Raspberry_Pi_Logo.svg",
                    style={
                        "height": "55px",
                        "position": "absolute",
                        "top": "10px",
                        "left": "10px"
                    }
                ),
                href="https://www.raspberrypi.com/",
                target="_blank"
            ),
            html.A(
                html.Img(
                    src="https://a.pololu-files.com/picture/0J7078.200h.jpg?4922c8bb56daed54a188c035bf8fa593",
                    style={
                        "height": "35px",
                        "position": "absolute",
                        "bottom": "10px",
                        "left": "12.5px"
                    }
                ),
                href="https://www.pololu.com/",
                target="_blank"
            ),
            html.A(
                html.Img(
                    src="https://cdn.freebiesupply.com/logos/thumbs/2x/arduino-1-logo.png",
                    style={
                        "height": "52px",
                        "position": "absolute",
                        "top": "10px",
                        "left": "55px"
                    }
                ),
                href="https://www.arduino.cc/",
                target="_blank"
            ),
            html.A(
                html.Img(
                    src="https://raw.githubusercontent.com/HARDWAREdotASTRO/HARDWAREdotASTRO.github.io/refs/heads/master/images/image00.png",
                    style={
                        "height": "52px",
                        "position": "absolute",
                        "top": "10px",
                        "left": "120px"
                    }
                ),
                href="https://github.com/HARDWAREdotASTRO",
                target="_blank"
            ),
            html.A(
                html.Img(
                    src="https://blogs.winona.edu/alumni/wp-content/uploads/sites/3/2021/03/WSU-Foundation-Logo-Purple.jpg",
                    style={
                        "height": "100px",
                        "position": "absolute",
                        "bottom": "10px",
                        "right": "10px"
                    }
                ),
                href="https://www.winona.edu/foundation/",
                target="_blank"
            ),
            html.A(
                html.Img(
                    src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTD4Zm2nU_ru4P_aw-465NI3EeRdRL9X0HETfj5z3sN5Y8kN8mY-Co7e8w&s=10",
                    style={
                        "height": "100px",
                        "position": "absolute",
                        "bottom": "10px",
                        "right": "193px"
                    }
                ),
                href="https://www.winona.edu/academics/colleges/science-engineering/physics-department/",
                target="_blank"
            ),
        ]
        )
    ],
        style={
            'padding': '0px 10px 15px 10px',
            'marginLeft': 'auto', 
            'marginRight': 'auto',
            "width": "900px",
            "height": "2225px",
            'boxShadow': '0px 0px 15px 10px rgba(204,204,204,0.4)',
        }
)

@app.callback(Output('live-date-time', 'children'),
              Input('interval-component', 'n_intervals'))
def update_metrics(n):
    return f"Current Date & Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

# Serial Monitor
@app.callback(
    Output("status-monitor", "value"), 
    [Input("placeholder2", "value")]
)

def serial_monitor(intervals):
    status = (
        "This application was developed to control the Winona State University Small Radio Telescope originally developed by MIT's Haystack Observatory. The telescope was donated to Winona State by Mayo High School in Rochester, Minnesota. The SRT includes a base and motors holding a 2.3m dish, allowing it to point over the entire sky. This graphical user interface controls the functions of the SRT."
    )

    return status

#Box Size will be disabled if Scan 
@app.callback(
    Output(component_id='boxSize', component_property='disabled'),
    [Input(component_id='select', component_property='value'),
    Input(component_id='scanner', component_property='value')]
)

def stateFunc3(selection, selection2):
    if selection == 'Scan' and selection2 == 'Obj':
        return False
    else:
        return True

#ScanSpeed will be disabled if scan is not on
@app.callback(
    Output(component_id='scanSpeed', component_property='disabled'),
    [Input(component_id='select', component_property='value')]
)

def stateFunc4(selection):
    if selection == 'Scan':
        return False
    else:
        return True

# Frequency Start and End will be disabled if Scan is not on
@app.callback(
    [Output(component_id='frequencyStart', component_property='disabled'),
     Output(component_id='frequencyEnd', component_property='disabled')],
    [Input(component_id='select', component_property='value')]
)

def frequencyState(selection):
    if selection == 'Scan':
        return False, False
    else:
        return True, True


# Connects RA and Dec coordinates to an Alt and Az output
@app.callback(
    Output(component_id='alt', component_property='children'),
    [Input(component_id='RA', component_property='value'),
     Input(component_id='DEC', component_property='value'),
     Input(component_id='go-button', component_property='n_clicks')]
)

def output_alt(RA, DEC, clicks):
    if clicks > prevclick:
        #When are ya observing
        observing_time = Time.now()
        #where are ya observing
        Winona = EarthLocation(lat='44.0554d', lon='-91.6664', height=202*u.m)
        #Stores loc and time
        aa = AltAz(location=Winona, obstime=observing_time)
        #Gets RA and Dec
        sky_locRAD = SkyCoord(RA, DEC, frame='icrs')
        #Splits off altitude in degrees
        alt = sky_locRAD.transform_to(aa).alt.deg
        #Must be above horizon (not sure thats what this is)
        is_positive = alt >= 0
        #Must be positive for rounding
        alt = abs(alt)
        #Puts into deg,min,sec
        minutes,seconds = divmod(alt*3600,60)
        degrees,minutes = divmod(minutes,60)
        #Converts back to negative if necessary
        degrees = degrees if is_positive else -degrees
        #Rounds
        deg =round(degrees)
        mins = round(minutes)
        sec = round(seconds)
        #Outputs in proper form
        alt2 = "{}°{}'{}''".format(deg, mins, sec)
        return alt2

#This is all the same as above just for Azimuth
@app.callback(
    Output(component_id='az', component_property='children'),
    [Input(component_id='RA', component_property='value'),
     Input(component_id='DEC', component_property='value'),
     Input(component_id='go-button', component_property='n_clicks')]
)


def output_az(RA, DEC, clicks):
    global prevclick
    if clicks > prevclick:
        observing_time = Time.now()
        Winona = EarthLocation(lat='44.0554d', lon='-91.6664', height=202*u.m)
        aa = AltAz(location=Winona, obstime=observing_time)
        sky_locRAD = SkyCoord(RA, DEC, frame='icrs')
        az = sky_locRAD.transform_to(aa).az.deg
        deg, mins, sec = degreeSpliterRounder(az)
        az2 = "{}°{}'{}''".format(deg, mins, sec)
        return az2
  

@app.callback(
    Output(component_id='go-home-button-count', component_property='children'),
    [Input(component_id='go-home-button', component_property='n_clicks')]
)

#Go home function for telescope store position
def goHomeButton(home_clicks):
    global homeprev
    if home_clicks > homeprev:
        #String to be sent to Arduino
        this_strAlt = "<0,3,9999,100>"
        this_strAz  = "<0,3,9999,100>"
        #Sends string to arduino
        ser2.write(str.encode(this_strAlt))
        ser1.write(str.encode(this_strAz))
        #Need to keep track of clicks(still not sure if necessary)
        homeprev = homeprev + 1

#Button to Stop motors
@app.callback(
    Output(component_id='stop-button-count', component_property='children'),
    [Input(component_id='stop-button', component_property='n_clicks')]
)

def StopButton(stop_clicks):
    #String to be sent to the Arduino
    this_strAlt = "<0,0>"
    this_strAz  = "<0,0>"
    #Sends string to the Arduino
    ser2.write(str.encode(this_strAlt))
    ser1.write(str.encode(this_strAz))

@app.callback(
    Output(component_id='zero-button-count', component_property='children'),
    [Input(component_id='zero-button', component_property='n_clicks')]
 )
 
def ZeroButton(zero_clicks):
    global zeroprev
    if zero_clicks > zeroprev:
        this_strAlt = "<0,4,9999,100>"
        this_strAz  = "<0,4,9999,100>"
        ser2.write(str.encode(this_strAlt))
        ser1.write(str.encode(this_strAz))
        zeroprev = zeroprev + 1

#Alt Direct Motor Control begins now
@app.callback(
    Output(component_id='alt-for-button-count', component_property='children'),
    [Input(component_id='alt-forward-button', component_property='n_clicks'),
    dash.dependencies.Input('alt-slider', 'value')]
)

#Changes the motor speed based on the slider
def AltForButton(alt_for_clicks, speed_alt):
    global altforprev
    if alt_for_clicks > altforprev:
        #The speed component is 3 spaces, the if statements allows for a 0 to come before a
        if speed_alt < 100:
            this_strAlt = "<0,1,9999,0{}>".format(speed_alt)
        if speed_alt == 100:
            this_strAlt = "<0,1,9999,{}>".format(speed_alt)
        if speed_alt < 10:
            this_strAlt = "<0,1,9999,00{}>".format(speed_alt)
        ser2.write(str.encode(this_strAlt))
        altforprev = altforprev + 1

@app.callback(
    Output(component_id='alt-rev-button-count', component_property='children'),
    [Input(component_id='alt-reverse-button', component_property='n_clicks'),
    dash.dependencies.Input('alt-slider', 'value')]
)

def AltRevButton(alt_rev_clicks, speed_alt):
    global altrevprev
    if alt_rev_clicks > altrevprev:
        if speed_alt < 100:
            this_strAlt = "<0,2,9999,0{}>".format(speed_alt)
        if speed_alt == 100:
            this_strAlt = "<0,2,9999,{}>".format(speed_alt)
        if speed_alt < 10:
            this_strAlt = "<0,2,9999,00{}>".format(speed_alt)
        ser2.write(str.encode(this_strAlt))
        altrevprev = altrevprev + 1

#Control motor speed for direct control
@app.callback(
    dash.dependencies.Output('speed-control-alt', 'children'),
    [dash.dependencies.Input('alt-slider', 'value')])

#This will only work up to 99
def AltSpeed(speed_alt):
    return 'PWM Duty Cycle = "{}"'.format(speed_alt)

#Azimuth Direct Motor Control Begins now
@app.callback(
    Output(component_id='az-for-button-count', component_property='children'),
    [Input(component_id='az-forward-button', component_property='n_clicks'),
    dash.dependencies.Input('az-slider', 'value')]
)

def AzForButton(az_for_clicks, speed_az):
    global azforprev
    if az_for_clicks > azforprev:
        if speed_az < 100:
            this_strAz = "<0,1,9999,0{}>".format(speed_az)
        if speed_az == 100:
            this_strAz = "<0,1,9999,{}>".format(speed_az)
        if speed_az < 10:
            this_strAz = "<0,1,9999,00{}>".format(speed_az)
        ser1.write(str.encode(this_strAz))
        azforprev = azforprev + 1

@app.callback(
    Output(component_id='az-rev-button-count', component_property='children'),
    [Input(component_id='az-reverse-button', component_property='n_clicks'),
    dash.dependencies.Input('az-slider', 'value')]
)

def AzRevButton(az_rev_clicks, speed_az): 
    global azrevprev
    if az_rev_clicks > azrevprev:
        if speed_az < 100:
            this_strAz = "<0,2,9999,0{}>".format(speed_az)
        if speed_az == 100:
            this_strAz = "<0,2,9999,{}>".format(speed_az)
        if speed_az < 10:
            this_strAz = "<0,2,9999,00{}>".format(speed_az)
        ser1.write(str.encode(this_strAz))
        azrevprev = azrevprev + 1

@app.callback(
    dash.dependencies.Output('speed-control-az', 'children'),
    [dash.dependencies.Input('az-slider', 'value')])

def AzSpeed(speed_az):
    return 'PWM Duty Cycle = "{}"'.format(speed_az)

#Callable function for converting decimals to rounded degree, minutes, seconds
def degreeSpliterRounder(angle):
    #Doesn't work for negatives
    is_positive = angle >= 0
    angle = abs(angle)
    #Actual seperation
    minutes,seconds = divmod(angle*3600,60)
    degrees,minutes = divmod(minutes,60)
    #Convert back to negative
    degrees = degrees if is_positive else -degrees
    #Round and return
    deg =round(degrees)
    mins = round(minutes)
    sec = round(seconds)
    return deg, mins, sec

#This is to output the motors actual location
@app.callback(
    Output(component_id='azimuth', component_property='children'),
    [Input(component_id='refresher', 
          component_property='n_intervals')]
)

def motorLocationAz(delay):
    global motAz
    #Request count from Arduino
    ser1.write(str.encode("<9>"))
    #Sometimes the read isn't timed right so allow an exception
    try:
        data =ser1.readline().decode('ascii')
        data1 = data.split(" ")
    except serial.serialutil.SerialException:
        return motAz
    #A partial read will give a bad number so dont process it
    try:
        location = int(data1[0])
    except ValueError:
        return motAz
    #Check which side of the gear the dish is on
    #Count is limited to about 2006 pulses
    if location <= 1003:
        #Convert to degrees
        azimuthDec = 90 * location / 1003
        #round
        az_deg = round(azimuthDec)
        #make string for return
        motAz = "{}°".format(az_deg)
        #reset data
        data = ''
        return motAz
    if location > 1003:
        azimuthDec = 90 - 90 * (location - 1003) / 1003
        az_deg = round(azimuthDec)
        motAz = "{}°".format(az_deg)
        data = ''
        return motAz
    #Continue returning previous MotAz
    else:
        return motAz

@app.callback(
    Output(component_id='altitude', component_property='children'),
    [Input(component_id='refresher2', 
          component_property='n_intervals')]
)

def motorLocationAlt(delay):
    global motAlt
    ser2.write(str.encode("<9>"))
    try:
        data =ser2.readline().decode('ascii')
        data2 = data.split(" ")
    except serial.serialutil.SerialException:
        return motAlt
    try:
        location = int(data2[0])
    except ValueError:
        return motAlt
    if location <= 1003:
        altitudeDec = 90 * location / 1003
        alt_deg = round(altitudeDec)
        motAlt = "{}°".format(alt_deg)
        data = ''
        return motAlt
    if location > 1003:
        altitudeDec = 90 - 90 * (location - 1003) / 1003
        alt_deg = round(altitudeDec)
        motAlt = "{}°".format(alt_deg)
        data = ''
        return motAlt
    else:
        return motAlt

@app.callback(
    Output('graph', 'figure'),
    [Input(component_id='refresher3', 
          component_property='n_intervals'),
    Input(component_id='solarsystem', component_property='value'),
    Input(component_id='RA', component_property='value'),
     Input(component_id='DEC', component_property='value'),
    Input(component_id='go-button', component_property='n_clicks')]
)

#Makes Graph with Sun, Moon and planets and trajectory of object of choice
def MakeGraph(delay, val, RA, DEC, clicks):
    #Need observation location
    Winona = EarthLocation(lat='44.0554d', lon='-91.6664', height=202*u.m)
    #Preps altitude and observation time
    aa = AltAz(location=Winona, obstime=Time.now())
    #Array of bodies to observe in the solar system
    Bodies = np.array(['sun', 'mercury', 'venus', 'mars', 'jupiter', 'saturn', 'uranus', 'neptune', 'moon'])
    #Create blank arrays to update in for loop
    BodyAz = np.array([])
    BodyAlt = np.array([])
    #Gets the Alt and Az for bodies in seperate arrays
    for i in Bodies:
        Bodycrd = get_body(i, Time.now(), Winona).icrs
        BodyAlt = np.append(BodyAlt,Bodycrd.transform_to(aa).alt.deg)
        BodyAz = np.append(BodyAz,Bodycrd.transform_to(aa).az.deg)
    if clicks != prevclick:
        BodAlt, BodAz = getAltAz2(val, RA, DEC)
        BodyAlt = np.append(BodyAlt, BodAlt) 
        BodyAz = np.append(BodyAz, BodAz) 
    #Names for displaying on graph
    SolarSystemNames = np.array(['Sun', 'Mercury', 'Venus', 'Mars', 'Jupiter', 'Saturn', 'Uranus', 'Neptune', 'Moon', 'Object'])
    #Unique sizes for different bodies
    SolarSizes = [25, 10, 10, 10, 15, 15, 15, 15, 25, 25]
    #Unique colors for different bodies
    SolarColors = ['yellow', 'grey', 'yellow', 'red', 'red', 'orange', 'blue', 'blue', 'grey', 'purple']
    #Call for object user is observing
    BodAz1, BodAlt1, BodAz2, BodAlt2 = getAltAz(val, RA, DEC)
    directions = ['N', 'E', 'S', 'W']
    directLoc = [0, 90, 180, 270]
    return {
        'data': [
                #Object observing
                go.Scatter(
                    name="Future",
                    x=BodAz1,
                    y=BodAlt1,
                ),
                #Trajectory of object observing
                go.Scatter(
                    name="Past",
                    x=BodAz2,
                    y=BodAlt2
                ),
                #Coordinates
                go.Scatter(
                    name="Sun",
                    x=BodyAz,
                    y=BodyAlt,
                    mode='markers',
                    text=SolarSystemNames,
                    marker={
                        'size': SolarSizes,
                        'color': SolarColors
                    }
                )
                ],
        "layout": go.Layout(
            #Set range
            xaxis={
                "title": "Azimuth", 
                "range": [0,360], 
                "ticktext":directions, 
                "tickvals":directLoc},
            yaxis={"title": "Altitude", 'range': [0, 90]},
            legend=dict(
                x=5,
                y=0.65,
                xanchor="left",
                yanchor="top",
                bgcolor="rgba(255,255,255,0.7)"
        ),
            margin={"l": 70, "b": 100, "t": 0, "r": 25}
        )
    }

def getAltAz2(val, RA, DEC):
    Winona = EarthLocation(lat='44.0554d', lon='-91.6664', height=202*u.m)
    timeNow=Time.now()
    #Predefined objects
    Body = SkyCoord(RA, DEC, frame='icrs')
    pointBody = AltAz(location=Winona, obstime=timeNow)
    BodAlt = Body.transform_to(pointBody).alt.deg
    BodAz = Body.transform_to(pointBody).az.deg
    return BodAlt, BodAz

#Call function for observing specified object
def getAltAz(val, RA, DEC):
    Winona = EarthLocation(lat='44.0554d', lon='-91.6664', height=202*u.m)
    timeNow=Time.now()
    #Predefined objects
    if val != 'object':
        Body = get_body(val, Time.now(), Winona).icrs
    #User specified object
    else:
        Body = SkyCoord(RA, DEC, frame='icrs')

    #Array for 24 hour period
    delta_hours = np.linspace(0, 12, 100)*u.hour
    full_night_times1 = timeNow + delta_hours
    full_night_times2 = timeNow - delta_hours
    #Creates array of alt az locations for this time
    full_night_aa_frames1 = AltAz(location=Winona, obstime=full_night_times1)
    full_night_aa_coos = Body.transform_to(full_night_aa_frames1).icrs
    #Location objects been
    BodAlt1 = Body.transform_to(full_night_aa_frames1).alt.deg
    BodAz1 = Body.transform_to(full_night_aa_frames1).az.deg
    #Location object will be (hopefully)
    full_night_aa_frames2 = AltAz(location=Winona, obstime=full_night_times2)
    full_night_aa_coos = Body.transform_to(full_night_aa_frames2).icrs

    BodAlt2 = Body.transform_to(full_night_aa_frames2).alt.deg
    BodAz2 = Body.transform_to(full_night_aa_frames2).az.deg
    #
    return BodAz1, BodAlt1, BodAz2, BodAlt2

#Moc hydrogen line test/live updating with sample data to see plot
def fetch_sdr_data(): #replace all this with data being read from SDR 
        frequencies = np.linspace(1420.0, 1420.8, 200)
        intensity = 10 + 5 * np.exp(-((frequencies - 1420.4)**2) / (0.05**2)) + np.random.normal(0, 0.5, 200)
        return frequencies, intensity

@app.callback(
    Output('live-hydrogen-graph', 'figure'),
    Input('interval-component1', 'n_intervals')
)
def update_graph_live(n):
    # Fetch latest SDR or backend telescope data
    freqs, intensity = fetch_sdr_data()

    # Create the Plotly Trace
    trace = go.Scatter(
        x=freqs,
        y=intensity,
        mode='lines',
        name='Antenna Temperature',
        line=dict(color='firebrick', width=2)
    )

    # Return the Figure Object
    return {
        'data': [trace],
        'layout': go.Layout(
            title='Live 1.42 GHz Neutral Hydrogen Emission',
            xaxis=dict(title='Frequency (MHz)', range=[1420.0, 1420.8]),
            yaxis=dict(title='Relative Intensity', range=[0, 20]),
            #template='plotly_dark' # Clean visual theme
        )
    }

if __name__ == '__main__':
    app.run(debug=True)