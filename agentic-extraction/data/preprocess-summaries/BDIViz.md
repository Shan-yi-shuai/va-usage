# Preprocess Summary: BDIViz

This file summarizes the preprocessing artifacts for one paper. The actual artifacts remain stored in their original locations. Use this file as the single entry point before running agentic extraction.

## Paper

This section identifies the paper.

```json
{
  "paper_name": "BDIViz",
  "paper_full_name": "BDIViz: An Interactive Visualization System for Biomedical Schema Matching with LLM-Powered Validation"
}
```

## Passages

This section points to the paragraph-level passage file extracted from the PDF.

```json
{
  "path": "data/passages/BDIViz_passages.json"
}
```

## Figures

This section points to the figure directory and embeds a condensed figure manifest. Each item only keeps the fields most useful for downstream extraction.

```json
{
  "directory": "data/figures/BDIViz",
  "items": [
    {
      "fig_id": "fig_1",
      "image_path": "data/figures/BDIViz/crops/fig_1.png",
      "caption": "Fig. 1: Biomedical data harmonization requires experts to manually match attributes across disparate datasets and schemas (1A-C).",
      "primary_role": "intended_workflow"
    },
    {
      "fig_id": "fig_2",
      "image_path": "data/figures/BDIViz/crops/fig_2.png",
      "caption": "Fig. 2: User-centered design approach. Left: Schema matching requirements (R1-R7) derived from expert interviews, color-coded (red: match discovery, green: value analysis, yellow: filtering). Right: Design considerations developed in iterative co-design sessions with domain experts (DC1-DC5). Colored lines between panels indicate the requirements and their corresponding design considerations.",
      "primary_role": "other"
    },
    {
      "fig_id": "fig_3",
      "image_path": "data/figures/BDIViz/crops/fig_3.png",
      "caption": "Fig. 3: The BDIViz interface includes: (1A) a shortcut panel for managing matching candidates, undo/redo, importing datasets, and exporting results as CSV or JSON; (1B) a control panel for filtering candidates; (1C) a timeline graph showing the history of user actions; (2A) an interactive heatmap panel displaying matching candidates with source attributes on the y-axis and target attributes displayed using a space-filling treemap layout on the x-axis; selected matches (cells) expand to show value distributions; (2B) bottom: an UpSet plot, value comparisons, and parallel coordinates for understanding the source-target relationships; (3A) agent explanation panel showing LLM validation results with reasoning (e.g., semantic match, shared tokens/values, historical references); (3B) display of target attribute properties, including node name, category, type, descriptions, and value distributions; and (4) a search bar to filter matches using keywords.",
      "primary_role": "interface"
    },
    {
      "fig_id": "fig_4",
      "image_path": "data/figures/BDIViz/crops/fig_4.png",
      "caption": "Fig. 4: (1) Interactive Heatmap cells; (2) Expanded view of the value distribution histograms for the source (2A) and target (2B) attributes shown when users click on a cell.",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_5",
      "image_path": "data/figures/BDIViz/crops/fig_5.png",
      "caption": "Fig. 5: Agent-derived explanations that take different aspect of matches into account.",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_6",
      "image_path": "data/figures/BDIViz/crops/fig_6.png",
      "caption": "Fig. 6: The UpSet Plot Panel displays (1) matcher weights, (2) the weighted average score for each candidate with the color corresponding to heatmap color palette, and (3) the matchers that produced a given candidate – shown as dots connected by line.",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_7",
      "image_path": "data/figures/BDIViz/crops/fig_7.png",
      "caption": "Fig. 7: NASA Task Load Index (TLX) Comparison Between BDIViz and Baseline. Box plots show workload scores (0-100) across 5 dimensions.",
      "primary_role": "evaluation"
    },
    {
      "fig_id": "fig_8",
      "image_path": "data/figures/BDIViz/crops/fig_8.png",
      "caption": "Fig. 8: Scatter plot comparing the average matching time and accuracy of BDIViz versus Manual methods across two tasks. The x-axis shows the average time (in minutes) per finished matching, while the circle size represents the correct rate (accuracy). Larger markers indicate higher accuracy, demonstrating that BDIViz consistently outperforms Manual curation by achieving faster and more accurate schema matching.",
      "primary_role": "evaluation"
    },
    {
      "fig_id": "fig_9",
      "image_path": "data/figures/BDIViz/crops/fig_9.png",
      "caption": "Fig. 9: Case Study 1: Heatmap visualization of curated matching candidates for Dou et al.’s endometrial carcinoma dataset to the GDC schema in the CPTAC-3 study.",
      "primary_role": "case_study"
    }
  ]
}
```

## View Images

This section points to the directory containing interface-view crops derived from the interface figure.

```json
{
  "directory": "data/view-images/BDIViz"
}
```
