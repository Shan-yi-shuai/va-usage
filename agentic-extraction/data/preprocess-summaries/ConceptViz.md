# Preprocess Summary: ConceptViz

This file summarizes the preprocessing artifacts for one paper. The actual artifacts remain stored in their original locations. Use this file as the single entry point before running agentic extraction.

## Paper

This section identifies the paper.

```json
{
  "paper_name": "ConceptViz",
  "paper_full_name": "ConceptViz: A Visual Analytics Approach for Exploring Concepts in Large Language Models"
}
```

## Passages

This section points to the paragraph-level passage file extracted from the PDF.

```json
{
  "path": "data/passages/ConceptViz_passages.json"
}
```

## Figures

This section points to the figure directory and embeds a condensed figure manifest. Each item only keeps the fields most useful for downstream extraction.

```json
{
  "directory": "data/figures/ConceptViz",
  "items": [
    {
      "fig_id": "fig_1",
      "image_path": "data/figures/ConceptViz/crops/fig_1.png",
      "caption": "Fig. 1: Our system for exploring and interpreting SAE features in LLMs consists of six interconnected views: (A) Concept Query View for building and refining queries, (B) SAE Discovery View for identifying relevant SAE models, (C) Feature Explorer View for browsing SAE features in concept space, (D) Feature Details View for examining semantic meaning of features, (E) Input Activation View for verifying response between features and concepts, and (F) Output Steering View for observing feature causal impact on model outputs.",
      "primary_role": "interface"
    },
    {
      "fig_id": "fig_2",
      "image_path": "data/figures/ConceptViz/crops/fig_2.png",
      "caption": "Fig. 2: SAEs address the polysemanticity problem in LLM neurons by projecting neuron activations into sparse, interpretable features. Each SAE feature corresponds to more specific human-understandable concepts (e.g., Duck, Yellow), enabling clearer semantic distinctions than the original neurons which may activate for multiple unrelated concepts.",
      "primary_role": "other"
    },
    {
      "fig_id": "fig_3",
      "image_path": "data/figures/ConceptViz/crops/fig_3.png",
      "caption": "Fig. 3: Our system’s three technical components: (A) Concept-based SAE Model Retrieval identifies relevant models by matching user queries with feature explanations, computing multi-threshold similarity rankings, and prioritizing consistently high-performing SAEs. (B) Feature Abstraction and Semantic Interpretation provides both global context through hierarchical clustering and topic visualization (B1), and detailed feature understanding through vocabulary projection and activation pattern analysis (B2). (C) Activation Analysis and Steering enables empirical validation through custom input testing and causal verification by manipulating feature activations to observe resulting output changes.",
      "primary_role": "other"
    },
    {
      "fig_id": "fig_4",
      "image_path": "data/figures/ConceptViz/crops/fig_4.png",
      "caption": "Fig. 4: Activation-similarity matrix visualization: Left: Well-explained feature with correlation between activation strength and semantic similarity (samples align along diagonal). Right: Poorly explained feature showing discrepancies - high-activation samples with low similarity (upper left) and high-similarity samples with low activation (lower right), revealing explanation limitations.",
      "primary_role": "view"
    },
    {
      "fig_id": "fig_5",
      "image_path": "data/figures/ConceptViz/crops/fig_5.png",
      "caption": "Fig. 5: A user exploring plant-related features: (A) The user queries “plant”, receives an optimized suggestion, then examines SAE relevance rankings with Layer 4 showing higher relevance. (B) While browsing feature clusters, the user identifies a relevant feature near the environmental region. (C) After selecting feature 983, the user examines its vocabulary space and activation matrix, revealing plant-related associations. (D) The user analyzes activations and validates through steering, observing effects on garden text generation.",
      "primary_role": "case_study"
    },
    {
      "fig_id": "fig_6",
      "image_path": "data/figures/ConceptViz/crops/fig_6.png",
      "caption": "Fig. 6: A user investigating superhero-related features: (A) The user identifies feature 6610 within the individuals cluster, referencing superhero characters. (B) Input activation shows strong responses to superhero names, while steering demonstrates control over character generation. (C) Most related features are distant with poor labels, but feature 9638’s proximity captures user interest. (D) Validation reveals feature 9638 activates for",
      "primary_role": "case_study"
    },
    {
      "fig_id": "fig_7",
      "image_path": "data/figures/ConceptViz/crops/fig_7.png",
      "caption": "Fig. 7: The results of the questionnaire regarding the effectiveness and usability of the visual system and workflow.",
      "primary_role": "evaluation"
    }
  ]
}
```

## View Images

This section points to the directory containing interface-view crops derived from the interface figure.

```json
{
  "directory": "data/view-images/ConceptViz"
}
```
