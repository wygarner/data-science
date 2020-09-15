import pandas as pd
import numpy as np

import dash
from dash.dependencies import Input, Output
import dash_html_components as html
import dash_core_components as dcc

import plotly_express as px
import plotly.figure_factory as ff


# Helpers
def calc_metrics(tn, fp, fn, tp, beta=0):
    """Calc acc, precision, recall, & f1 from confusion matrix"""
    if beta is None:
        beta = 0

    metrics = {}
    n = tn + fp + fn + tp
    metrics['Accuracy'] = (tp + tn) / n
    metrics['Precision'] = tp / (tp + fp)
    metrics['Recall'] = tp / (tp + fn)
    metrics['F1'] = 2 * ((metrics['Precision'] * metrics['Recall']) /
                         (metrics['Precision'] + metrics['Recall']))

    metrics[f'F1 Beta (beta = {beta:.2f})'] = (1 + beta ** 2) * ((metrics['Precision'] * metrics['Recall']) /
                                                                 (beta ** 2 * metrics['Precision'] + metrics['Recall']))

    return metrics


def gen_slider(title, slider_id, min_val=0, max_val=500, step=25, value=250):
    """Helper to generate a slider with a title and displayed value"""
    return html.Div([html.H6(title),
                     dcc.Slider(
                         id=slider_id,
                         min=min_val,
                         max=max_val,
                         step=step,
                         value=value,
                         tooltip={'always_visible': True,
                                  'placement': 'bottom'},
                     )])


# Make stuff pretty
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# Structure of the app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
app.layout = html.Div([
    html.H5('Confusion Matrix'),
    # Confusion matrix input sliders
    html.Div([
        html.Div([
            gen_slider('N True Negatives', slider_id='n_tn_slider', value=250),
            gen_slider('N False Negatives', slider_id='n_fn_slider', value=100),
        ]),
        html.Div([
            gen_slider('N False Positives', slider_id='n_fp_slider', value=100),
            gen_slider('N True Positives', slider_id='n_tp_slider', value=250),
        ]),
    ], style={
        'width': '50%',
        'columnCount': 2,
    }),
    html.Hr(),
    html.Div([
        # Beta numeric input for F1-beta calc
        html.Div([
            html.H6('F1 Beta'),
            dcc.Input(
                id='f1_beta',
                type='number',
                placeholder='F1 Beta',
                value=0.5, min=0, max=100, step=0.1,
            ),
        ], style={'margin-left': '55%'}),
    ]),
    # Plots
    html.Div([
        html.Div([
            dcc.Graph(id='confusion_matrix',
                      config={'displayModeBar': False},
                      ),
            html.Br(),
        ], style={'marginBottom': '3em'}),
        html.Div([
            dcc.Graph(id='metric_bar_graph',
                      config={'displayModeBar': False},
                      ),
        ]),
    ], style={
        'width': '100%',
        'columnCount': 2,
    }),
])


@app.callback(
    Output('confusion_matrix', 'figure'),
    [Input('n_tn_slider', 'value'),
     Input('n_fp_slider', 'value'),
     Input('n_fn_slider', 'value'),
     Input('n_tp_slider', 'value'), ])
def update_confusion_matrix(tn, fp, fn, tp):
    """Plot confusion matrix as a heatmap"""
    z = np.array([[fn, tp],
                  [tn, fp]])
    n = z.sum()
    z = z / n
    z = z.round(2)

    x = ['Predicted Negative', 'Predicted Positive']
    y = ['Actual Positive', 'Actual Negative']

    fig = ff.create_annotated_heatmap(z, x=x, y=y, colorscale='Cividis')
    fig.update_layout(title={'xanchor': 'center',
                             'x': 0.545,
                             'text': f'Proportions of Confusion (n={n})'})

    return fig


@app.callback(
    Output('metric_bar_graph', 'figure'),
    [Input('n_tn_slider', 'value'),
     Input('n_fp_slider', 'value'),
     Input('n_fn_slider', 'value'),
     Input('n_tp_slider', 'value'),
     Input('f1_beta', 'value'), ]
)
def update_metric_bar_graph(tn, fp, fn, tp, beta):
    """Plot classification metrics as a bar chart"""
    m = calc_metrics(tn, fp, fn, tp, beta)
    metric_df = pd.DataFrame({'Metric': list(m.keys()),
                              'Value': list(m.values())})
    metric_df['display_value'] = round(metric_df['Value'], 3)

    fig = px.bar(metric_df,
                 x='Metric',
                 y='Value',
                 color='Metric',
                 text='display_value')
    fig.update_yaxes(range=[0, 1])
    fig.layout.update(showlegend=True,
                      title={'xanchor': 'center',
                             'x': 0.5,
                             'text': 'Accuracy Metrics'})

    return fig


if __name__ == '__main__':
    app.run_server(debug=False)
