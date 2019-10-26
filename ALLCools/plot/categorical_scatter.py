import seaborn as sns
from matplotlib.lines import Line2D

from .color import level_one_palette
from .text_anno_scatter import _text_anno_scatter
from .utilities import _make_tiny_axis_label, _density_based_sample, _extract_coords


def categorical_scatter(
        data,
        ax,
        coord_base='umap',
        x=None,
        y=None,
        scatter_kws=None,
        hue=None,
        palette='auto',
        text_anno=None,
        dodge_text=False,
        dodge_kws=None,
        text_anno_kws=None,
        text_anno_palette=None,
        text_transform=None,
        show_legend=False,
        legend_kws=None,
        emphasize_by_size: dict = None,
        sizes: dict = None,
        axis_format='tiny',
        max_points=5000,
        labelsize=4,
        s=5
):
    """
    Plot scatter plot with these options:
    - Color by a categorical variable, and generate legend of the variable if needed
    - Add text annotation using a categorical variable
    - Emphasize certain category by different scatter size,
      but using different size for more than 2 categories is probably not a good idea.

    Parameters
    ----------
    data
        Dataframe that contains coordinates and categorical variables
    ax
        this function do not generate ax, must provide an ax
    coord_base
        coords name, if provided, will automatically search for x and y
    x
        x coord name
    y
        y coord name
    scatter_kws
        kws dict pass to sns.scatterplot
    hue
        col name or series
    palette
        palette of the hue, str or dict
    text_anno
        col name or series
    dodge_text
    dodge_kws
    text_anno_kws
    text_anno_palette
    text_transform
    show_legend
    legend_kws
    emphasize_by_size
    sizes
    axis_format
    max_points
    labelsize
    s

    Returns
    -------

    """
    # add coords
    _data, x, y = _extract_coords(data, coord_base, x, y)
    # _data has 2 cols: "x" and "y"

    # down sample plot data if needed.
    if max_points is not None:
        if _data.shape[0] > max_points:
            _data = _density_based_sample(_data, seed=1, size=max_points,
                                          coords=['x', 'y'])

    # default scatter options
    _scatter_kws = {'linewidth': 0, 's': s, 'legend': None, 'palette': palette}
    if scatter_kws is not None:
        _scatter_kws.update(scatter_kws)

    # deal with color
    palette_dict = None
    if hue is not None:
        if isinstance(hue, str):
            _data['hue'] = data[hue]
        else:
            _data['hue'] = hue
        hue = 'hue'
        _data['hue'] = _data['hue'].astype('category')
        # deal with color palette
        palette = _scatter_kws['palette']
        if isinstance(palette, str) or isinstance(palette, list):
            palette_dict = level_one_palette(_data['hue'], order=None, palette=palette)
        elif isinstance(palette, dict):
            palette_dict = palette
        else:
            raise TypeError(f'Palette can only be str, list or dict, '
                            f'got {type(palette)}')
        _scatter_kws['palette'] = palette_dict

    # deal with size
    s = _scatter_kws.pop('s')
    if emphasize_by_size is not None:
        if sizes is None:
            raise ValueError('sizes must be provided together with emphasize_by_size.')
        _data['size'] = data[emphasize_by_size]
        _data['size'] = _data['size'].apply(lambda i: sizes[i] if i in sizes else s)
    else:
        _data['size'] = s
    _scatter_kws['s'] = _data['size'].values
    # here I do not use sns.scatterplot size option, but directly use ax.scatter s option

    sns.scatterplot(x='x', y='y', hue=hue,
                    data=_data, ax=ax, **_scatter_kws)

    # deal with text annotation
    if text_anno:
        if isinstance(text_anno, str):
            _data['text_anno'] = data[text_anno]
        else:
            _data['text_anno'] = text_anno

        _text_anno_scatter(data=_data[['x', 'y', 'text_anno']],
                           ax=ax,
                           x='x',
                           y='y',
                           dodge_text=dodge_text,
                           dodge_kws=dodge_kws,
                           palette=text_anno_palette,
                           text_transform=text_transform,
                           anno_col='text_anno',
                           text_anno_kws=text_anno_kws,
                           labelsize=labelsize)

    # clean axis
    if axis_format == 'tiny':
        _make_tiny_axis_label(ax, x, y, arrow_kws=None, fontsize=labelsize)
    elif (axis_format == 'empty') or (axis_format is None):
        sns.despine(ax=ax, left=True, bottom=True)
        ax.set(xticks=[], yticks=[], xlabel=None, ylabel=None)
    else:
        pass

    # deal with legend
    if show_legend and (hue is not None):
        n_hue = len(palette_dict)
        _legend_kws = dict(ncol=(1 if n_hue <= 20 else 2 if n_hue <= 40 else 3),
                           fontsize=labelsize,
                           bbox_to_anchor=(1.05, 1),
                           loc='upper left',
                           borderaxespad=0.)
        if legend_kws is not None:
            _legend_kws.update(legend_kws)

        handles = []
        labels = []
        exist_hues = _data['hue'].unique()
        for hue_name, color in palette_dict.items():
            if hue_name not in exist_hues:
                # skip hue_name that do not appear in the plot
                continue
            handle = Line2D([0], [0], marker='o', color='w',
                            markerfacecolor=color, markersize=_legend_kws['fontsize'])
            handles.append(handle)
            labels.append(hue_name)
        _legend_kws['handles'] = handles
        _legend_kws['labels'] = labels
        ax.legend(**_legend_kws)
    return ax, _data
