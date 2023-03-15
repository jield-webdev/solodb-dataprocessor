import matplotlib as mpl
import numpy as np
mpl.use('Agg')

import matplotlib.pyplot as plt 
import pandas as pd

from flask import send_file
from io import BytesIO

labels = {
  "fwhm": "FWHM [$cm^{-1}$]",
  "a": "Amplitude [a.u.]",
  "w": "Wavenumber [$cm^{-1}$]",
  "doping": "Doping [$cm^{-2}$]",
  "strain": "Strain [%]",
  "sanity": "Sanity Check"
}

def to_label(key):
  k = key.split("_")
  label = ""
  if len(k)>1:
    label += k[0].upper() + "-Peak "
  label += labels[k[-1]]
  return label

def histogram(dfs, args: dict):
  setup(args)
  key = args["config"].get("key", "g_w")
  for df in dfs:
    plt.hist(df[key], 100, density=True, alpha=0.3)

  plt.xlabel(to_label(key))
  plt.ylabel("density")

  return send_fig()


  setup(args)
  key = args["config"].get("key", "g_w")

  df = dfs[0] #comparison impossible TODO find a better way
  pos = np.stack([df["pos_x"],df["pos_y"]], axis=-1)
  print(df)
  plot_heatmap(
    ampl=df[key],
    positions=pos,
    title=to_label(key),
    ax=plt.gca()
  )
  return send_fig()


  x_map = np.sort(np.array(list(set(positions[:,0]))))
  y_map = np.sort(np.array(list(set(positions[:,1]))))
  x_map = x_map - np.mean(x_map)
  y_map = y_map - np.mean(y_map)
  #print(y_map.shape, x_map.shape)
  dx = x_map[1] - x_map[0]
  dy = y_map[1] - y_map[0]

  heatmap_data = pd.DataFrame(np.zeros((len(x_map), len(y_map))))
  iterator = 0
  for n in range(len(y_map)):
    for i in range(len(x_map)):
      heatmap_data.iloc[len(x_map)-1 - i, len(y_map)-1 - n] = ampl[iterator]
      iterator = iterator + 1
  if not ax:
    fig_heatmap = plt.figure()
    ax = plt.gca()
  else:
    fig_heatmap = None
    plt.sca(ax)
  if transpose:
    heatmap_data = heatmap_data.transpose()
  plt.imshow(heatmap_data, cmap='magma', extent=[x_map[-1]+dx/2, x_map[0]-dx/2, y_map[-1]+dy/2, y_map[0]-dy/2],
    vmin = np.nanquantile(heatmap_data, 0.02), vmax = np.nanquantile(heatmap_data, 0.98))
  plt.colorbar()
  ax.set(title=title, xlabel='x (µm)', ylabel='y (µm)')
  return fig_heatmap, ax


  axd = fig.subplot_mosaic(
    [
        ["g_kde"  , "empty"],
        ["scatter", "2d_kde"],
    ],
    height_ratios=[1, 5],
    width_ratios=[5, 1],
  )
  axd["scatter"].get_shared_x_axes().join(axd["g_kde"], axd["scatter"])
  axd["g_kde"].set_xticklabels([])
  axd["scatter"].get_shared_y_axes().join(axd["2d_kde"], axd["scatter"])
  axd["2d_kde"].set_yticklabels([])
  axd["empty"].axis("off")

  ax = axd["scatter"]
  ax.grid()
  xlim = np.array([1575, 1605])
  ylim = [2650, 2700]
  linewidth = 0.2
  ax.set_xlim(xlim)
  ax.set_ylim(ylim)
  ax.set_xlabel(to_label("g_w"))
  ax.set_ylabel(to_label("2d_w"))
  doping_lim = (0.7 * (xlim - 1581.6)) + 2676.9 
  strain_lim = (2.2 * (xlim - 1581.6)) + 2676.9
  ax.plot(xlim, doping_lim, "k", linewidth=linewidth)
  ax.plot(xlim, strain_lim, "k", linewidth=linewidth)
  ax.scatter(1581.6, 2676.9, s=100, marker='o', 
      facecolor="none", edgecolor="k", linewidth=linewidth)
  # ax.text(1580, 2690, 'Strain')
  # ax.text(1597, 2681, 'Doping')


  for df in dfs:
    ax.scatter(df["g_w"], df["2d_w"], alpha=10*np.sqrt(1/len(df)),
        marker=".", edgecolors="none", s=2)
  
  from scipy.stats import gaussian_kde
  for df in dfs:
    plt.sca(axd["2d_kde"])
    ax = plt.gca()
    gkde = gaussian_kde(df["2d_w"].dropna())
    y = np.linspace(*ylim, 150)
    plt.plot(gkde(y), y)
    plt.xticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)

    plt.sca(axd["g_kde"])
    ax = plt.gca()
    df["g_w"].plot(kind='density', ax=axd["g_kde"])
    plt.ylabel("")
    plt.yticks([])
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['left'].set_visible(False)
  
  return send_fig()

def setup(args):
  return plt.figure(figsize=(args["figsize_x"], args["figsize_y"]), constrained_layout=True)

def send_fig():
  img = BytesIO()
  plt.savefig(img)
  img.seek(0)
  return send_file(img, mimetype='image/png')