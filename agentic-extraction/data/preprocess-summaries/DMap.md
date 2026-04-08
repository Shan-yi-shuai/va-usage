# Preprocess Summary: DMap

This file summarizes the preprocessing artifacts for one paper. The actual artifacts remain stored in their original locations. Use this file as the single entry point before running agentic extraction.

## Paper

This section identifies the paper.

```json
{
  "paper_name": "DMap",
  "paper_full_name": "D-Map: Visual analysis of ego-centric information diffusion patterns in social media"
}
```

## Passages

This section points to the paragraph-level passage file extracted from the PDF.

```json
{
  "path": "data/passages/DMap_passages.json"
}
```

## Figures

This section points to the figure directory and embeds a condensed figure manifest. Each item only keeps the fields most useful for downstream extraction.

```json
{
  "directory": "data/figures/DMap",
  "items": [
    {
      "fig_id": "fig_1",
      "image_path": "data/figures/DMap/crops/fig_1.png",
      "caption": "Figure 1: System Interface: Source Weibo Table View (a), for selecting different groups of source weibos; Source Weibo Distribution View (b), including Documents View (b1) and Keywords View (b2); D-Map View (c), summarizing the social interaction among participating people of a central user; Community Radar View (d), showing the high dimensional features of communities with a Radar View (d1) and a Statistics Information Window (d2); Hierarchical View (e), illustrating the reposting structures; Timeline View (f), highlighting the temporal trends of the diffusion; Small Multiple View (g), identifying key time frames of D-Map’s snapshots.",
      "primary_role": "interface"
    },
    {
      "fig_id": "fig_2",
      "image_path": "data/figures/DMap/crops/fig_2.png",
      "caption": "Figure 2: An illustration of the weibo data. People play different roles in one central user’s reposting network with multiple behaviors.",
      "primary_role": "other"
    },
    {
      "fig_id": "fig_3",
      "image_path": "data/figures/DMap/crops/fig_3.png",
      "caption": "Figure 3: Conceptual model illustrating the diffusion process. Starting from a central user, information diffuses within and across multiple communities through a series of reposting behaviors.",
      "primary_role": "other"
    },
    {
      "fig_id": "fig_4",
      "image_path": "data/figures/DMap/crops/fig_4.png",
      "caption": "Figure 4: Visual encodings of D-Map of a central user. Each node represents a group of people, participating in the diffusion process by reposting weibos.",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_5",
      "image_path": "data/figures/DMap/crops/fig_5.png",
      "caption": "Figure 5: Color decision for D-Map. Four series of color encode the high-dimensional features of the community. The radar visualization shows the distribution of each dimension of selected communities.",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_6",
      "image_path": "data/figures/DMap/crops/fig_6.png",
      "caption": "Figure 6: D-Map construction process. With the input of a series of source weibos from a central user and the reposting trees of these source weibos, we can merge them into a graph, compact the layout and reorder nodes in each community based on chronological order.",
      "primary_role": "intended_workflow"
    },
    {
      "fig_id": "fig_7",
      "image_path": "data/figures/DMap/crops/fig_7.png",
      "caption": "Figure 7: Merging thresholds for the size control. (a) Set the hex-bin number as 1000. (b) Maximize the number ( 9,000 in this case).",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_8",
      "image_path": "data/figures/DMap/crops/fig_8.png",
      "caption": "Figure 8: Visual analysis pipeline, illustrating how to explore users’ D-Map with the augmented trend, hierarchy and high dimensional analysis. Diffusion path, social interactions and people impact can be found.",
      "primary_role": "intended_workflow"
    },
    {
      "fig_id": "fig_9",
      "image_path": "data/figures/DMap/crops/fig_9.png",
      "caption": "Figure 9: Weibo sources analysis with (a) reposting people distribution distance and (c) document distance. Interactions including (b) brushing and (c) keyword filtering are supported.",
      "primary_role": "case_study"
    },
    {
      "fig_id": "fig_10",
      "image_path": "data/figures/DMap/crops/fig_10.png",
      "caption": "Figure 10: Dynamic diffusion pattern analysis. (a) Multiple diffusion stages are shown in the small multiples and the timeline. (b) By interactively exploring the communities, we find key players and summarize diffusion patterns.",
      "primary_role": "case_study"
    },
    {
      "fig_id": "fig_11",
      "image_path": "data/figures/DMap/crops/fig_11.png",
      "caption": "Figure 11: Community analysis on D-Map. Users can have an overview on the (a) D-Map and (b) Community Radar View. By selecting the community, users can explore the characteristics (e, f). (d) Timeline View, (c) Hierarchical View and (g) Small Multiple View are provided to investigate different aspects of the diffusion process. Users can explore the detailed (h) inter-community behaviors and (i) key player behaviors.",
      "primary_role": "interface"
    },
    {
      "fig_id": "fig_12",
      "image_path": "data/figures/DMap/crops/fig_12.png",
      "caption": "Figure 12: People portrait visualization from D-Map. We can differentiate people from multiple dimensions. Two dimensions showing here are the split community number and inter-community influence. We can see from the top-left, where there is merely communications among a few communities, to the bottom-right with the influence pattern in multiple, evenly-distributed communities.",
      "primary_role": "view"
    }
  ]
}
```

## View Images

This section points to the directory containing interface-view crops derived from the interface figure.

```json
{
  "directory": "data/view-images/DMap"
}
```
