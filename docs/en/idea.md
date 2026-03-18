# Idea

## Title

**Pets in the Loop**

---

## Story

**Introduction:**  
"The next wave is Physical AI." That phrase is now heard everywhere. Software has already achieved much of what it can, and the next era is one in which AI has a body. In 10 to 20 years, it is highly likely that robots will enter households. When that happens, who will be living in the home? Not only humans. Pets such as cats will be there too.

**Development:**  
At the earliest stage of brainstorming, we were thinking only about products in the context of "human × AI." Human in the Loop, collaboration with AI, tools that enrich human experience... before we knew it, every design decision centered on humans. Then we had a sudden realization: "We had completely forgotten about animals." AI is becoming a familiar tool for humans, but what about animals? Most future predictions still discuss AI almost exclusively in the context of "human × AI."

**Turn:**  
Our reinterpretation of Brand New: "Brand New 'Hello World.'" The core message of this theme is probably to create a new common sense. We added our own interpretation. The phrase "Brand New" also contains the nuance of something unused and untouched. AI may no longer be brand new for humans. But for animals, the emergence of Physical AI may become their Hello World to a new kind of AI, because for the first time they may gain an interface they can interact with that is not limited to humans. Our "Brand New Hello World." may be understood as creating the very first moment in which an animal encounters AI.

**Conclusion:**  
In a future where Physical AI is widespread, pets will interact with AI in everyday life through robots and other hardware. Their reactions will help train the model. Pets enter the loop. In addition, human annotation is essential for creating ground-truth data, and the model can evolve only when the cat's reaction feedback is combined with human knowledge. Through this hackathon, we want to propose a new concept: **Pets in the Loop**. With the coming age of Physical AI, both humans and animals can contribute to the development of AI through different functions. We aim to let people preview that future through a Web experience built with today's technology.

> **On the naming:**  
> We initially considered "Animal in the Loop," but renamed it because the same concept had already been proposed elsewhere.  
> In this product, human annotation for creating ground-truth data and model improvement through cat reactions function as two wheels of the same vehicle, so we adopted **Pets in the Loop** as the concept name.

---

## Product Proposal

### Product Name
TBD

### Premise

- **Background:** We considered the nature of a hackathon, the difficulty of procuring hardware such as robotics, and overall cost.
- **Strategy:** Build a cat-focused **future-experience Web app** as the MVP.

---

## System Architecture

### [1. Input Layer] Multimodal Analysis

**Audio analysis (.wav)**
- Model: `IsolaHGVIS/Cat-Meow-Classification` (HuggingFace)
- Architecture: CNN + Mel Spectrogram (`128×174×1`)
- Output classes: `brushing` / `waiting_for_food` / `isolation`
- Deployment: loaded locally from HuggingFace at no cost

**Image analysis 1: Cat face**
- Model: `semihdervis/cat-emotion-classifier` (HuggingFace)
- Base model: ViT (`google/vit-base-patch16-224-in21k`)
- Output classes: `happy` / `sad` / `angry`
- Deployment: loaded locally from HuggingFace at no cost

**Image analysis 2: Full-body pose estimation for cats (ViTPose++)**
- Model: `usyd-community/vitpose-plus-plus-small` (HuggingFace)
- Architecture: Vision Transformer + MoE decoder
- Head: AP-10K head (`dataset_index=3`)
- Output: 17 body keypoints × (`x`, `y`, `confidence`) = 51 dimensions
- Relative angles are derived for the tail, ears, and body axis from the detected points
- Deployment: loaded with HuggingFace `transformers` (`VitPoseForPoseEstimation`) at no cost

**Image analysis 3: Zero-shot state classification for cats (CLIP)**
- Model: `openai/clip-vit-base-patch32` (HuggingFace)
- Architecture: Vision Transformer + text encoder
- Output: similarity scores to custom prompts such as `"interested cat"` and `"relaxed cat"`
- Feature: arbitrary state labels can be defined in a zero-shot manner, which works well with human-designed annotation schemes
- Deployment: loaded with HuggingFace `transformers` (`CLIPModel`) at no cost

**Environmental information**
- OpenWeatherMap API + browser `Date()`
- Data: temperature and time of day

**[Logic]:** Generate a state key by combining audio output, face classification output, pose keypoint output, CLIP score output, and environmental information.

> **Note:** The exact logic for integrating audio and image model outputs, as well as the detailed design of the state key, will be determined in a later ML tuning phase. At this stage, the outputs of each model will be used directly.

### [2. Bandit Layer] Optimization Logic

> The detailed algorithm and parameters for this layer are still to be determined. The following is idea-level content.

- Candidate algorithm: UCB (Upper Confidence Bound), etc.
- Processing: choose and explore "the video to show right now" from a template library of roughly 40 to 50 initial options based on the state key
- Infrastructure: planned deployment on Vertex AI (GCP)

### [3. Generation Layer] AI Orchestration

- **Gemini (GCP / Vertex AI):** generate a video-generation prompt from the selected template and the current state
- **Veo3 (GCP):** generate a cat-oriented video from the prompt

### [4. Output Layer]

- Deliver the video in a Web browser and play it on a screen intended for the cat.

### [5. Feedback Layer] Reward Calculation

> The reward design is still to be determined. The following is idea-level content.

- Re-sampling: after playback, sample audio and image again
- Reward definition proposal: reward = post-video score - pre-video score
- Persistence: store the Bandit table in Cloud Firestore (GCP)

### [6. Template Evolution Layer] Autonomous Improvement

> The detailed specification for this layer is still to be determined. The following is idea-level content.

- Elimination: automatically discard templates that continuously fall below the overall average reward
- Evolution: Gemini autonomously generates and adds new templates to extend the library

---

## Web App Design

### Two-mode configuration

```text
┌──────────────────────────────────────────┐
│               PawPlay                    │
│                                          │
│  [ Experience Mode (for judges) ]        │
│  [ Production Mode (real cat data) ]     │
└──────────────────────────────────────────┘
```

### Experience Mode (live demo for judges)

The concept is "You become the cat." Judges experience the product directly. Two input routes are prepared, including a fallback path.

#### Input Method A: Select from prepared samples

1. Choose a cat meow.
2. Choose a cat face photo.
3. Acquire environment information automatically.

#### Input Method B: Real voice and image

1. Meow into the microphone like a cat.
2. Take a "cat-like face" photo with the camera.

If analysis fails, the flow automatically falls back to Input Method A.

### Shared Output Screen

- Show the state key, selected template, and generation progress.
- Play the generated video in full screen.
- Collect user feedback with three choices: excited / okay / not interested.

### Production Mode (real cat data)

1. Upload data: `.wav`, `.jpg`, and environment information.
2. Run analysis and generation: each model analyzes the input, a state key is generated, Bandit selects a template, Gemini rewrites the prompt, and Veo3 generates the video.
3. Post-evaluation loop: after playback, obtain post-state data manually or automatically and update the Bandit table.

---

## What Pets in the Loop Means

The "loop" in this product is established through **collaboration between humans and cats**.

**Loop 1: In-session loop**  
The cat watches the video, its reaction is scored, and the result is recorded as reward.

**Loop 2: Cross-session learning**  
Accumulated rewards update the Bandit table, improving future selections. This is the state in which **cats are training the model**.

**Loop 3: Human annotation**  
Humans create and label the ground-truth data. By combining cat reaction data with human knowledge, the improvement loop becomes complete. This is the state in which **humans and cats are collaboratively training AI**.

**Loop 4: Library evolution**  
Low-rated templates are discarded and Gemini autonomously generates new ones, allowing the entire library to evolve.

**"Humans and cats teaching AI together" is the essential meaning of Pets in the Loop.**

---

## Base Model Development Flow

1. **Prototype recording:** capture at least 30 examples of "state × video × reaction" with one cat.
2. **Feature analysis:** determine which variables matter most among facial emotion scores, pose keypoints, CLIP scores, temperature, and time.
3. **Human annotation:** have humans label the collected data to build an initial ground-truth set.
4. **Initial table construction:** assign at least one initial score to every template.
5. **Deployment:** implement the result as the base model.
6. **Day-of operation:** reflect additional demo data in the table in real time.

---

## Technology and Infrastructure

### Cat analysis models (HuggingFace / GitHub, free)

| Purpose | Model ID | Base | Output | License |
|---|---|---|---|---|
| Cat face emotion classification | `semihdervis/cat-emotion-classifier` | ViT-base | happy / sad / angry | Apache 2.0 |
| Full-body cat pose estimation | `usyd-community/vitpose-plus-plus-small` | ViT + MoE (AP-10K head) | 17 body keypoints × (`x`, `y`, `conf`) | Apache 2.0 |
| Zero-shot cat state classification | `openai/clip-vit-base-patch32` | CLIP ViT-B/32 | similarity score to custom prompts | MIT |
| Cat meow classification | `IsolaHGVIS/Cat-Meow-Classification` | CNN + Mel Spectrogram | brushing / waiting_for_food / isolation | MIT |

> **Policy:** Load cat-analysis models locally from HuggingFace / GitHub without external API billing.

### GCP products

| Purpose | GCP product |
|---|---|
| Video generation | Veo3 |
| Prompt generation and template evolution | Gemini (Vertex AI) |
| Bandit model deployment and inference | Vertex AI |
| Data persistence | Cloud Firestore |
| Model fine-tuning if needed | Vertex AI |

---

## Alignment With Hackathon Requirements

| Category | Item | How this proposal responds |
|---|---|---|
| Theme | a | A convincing reversal of human-centered design through the idea of AI for animals |
| Theme | b | An empathetic story in which human × AI thinking unexpectedly led us to cats |
| Theme | c | A clear answer that AI remains an unopened "Brand New" existence for animals |
| Reproducibility | a | Both a recorded demo and a judge-participation live demo |
| Reproducibility | b | A Web app format that could reach households with pets in Japan |
| Reproducibility | c | Robust design with Firestore persistence and fallbacks |
| Google technology | a | Advanced UX built from Gemini, Veo3, and GCP |
| Google technology | b | Vertex AI deployment, fine-tuning, and autonomous generation with Gemini |
| Google technology | c | High technical integration by completing all non-cat-analysis processing on GCP |
| Unconventionality | a | An unusual stack: cat face + pose keypoints + CLIP scores -> Bandit -> Gemini -> Veo3 |
| Unconventionality | b | The strong presentation impact of having judges become cats |
| Unconventionality | c | A novel but hands-on production method using real cat data and human annotation |

---

## Legend (Evaluation Criteria)

**Theme**
- a. Does the product and presentation convincingly align with the theme?
- b. Is there an empathetic story behind the thinking and process that led to the product?
- c. Is the answer to the theme "Brand New 'Hello World.'" both clear and genuinely brand new?

**Reproducibility of the product**
- a. Can the product be demonstrated and achieve its purpose?
- b. Is it delivered in a form that can reach and be used by many people?
- c. Does the design consider robustness and extensibility, including error handling and load measures?

**Use of Google technology**
- a. Are Google technologies used effectively and at a high level to realize strong functionality and experience?
- b. Are Google AI technologies such as Gemma, Gemini, and Vertex AI used effectively in development and in the product itself?
- c. Overall, is the technical implementation difficult and the product highly complete?

**Unconventionality**
- a. Uses a technical stack that would not normally be conceived
- b. Leaves a strong impression through presentation
- c. Uses an unusual production process
