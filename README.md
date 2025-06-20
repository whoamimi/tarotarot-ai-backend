# Taro Tarot AI ML/AI Hub

Taro's development Fast API.

# Overview
**Broad Meta Categories**
	•	Emotional Life: Love, Relationships, Friendships
	•	Practical Life: Career, Finance, Health
	•	Foundational: Family, Home, Stability
	•	Existential: Spirituality, Growth, Purpose

**In-depth**

| **Label**                      | **Description / Example Questions**                                                                 |
|-------------------------------|------------------------------------------------------------------------------------------------------|
| **Love & Relationships**      | Romantic interests, soulmates, breakups, dating. <br> _"Will I meet someone soon?"_                 |
| **Career & Ambitions**        | Career moves, promotions, purpose. <br> _"Should I change jobs?"_                                   |
| **Finance & Wealth**          | Money, savings, financial struggles. <br> _"Will I be financially stable?"_                         |
| **Health & Wellness**         | Physical, mental, emotional well-being. <br> _"How can I improve my health?"_                       |
| **Family & Home**             | Family dynamics, children, living situation. <br> _"Will my home life become more peaceful?"_       |
| **Personal Growth**           | Healing, self-discovery, learning. <br> _"How can I grow emotionally?"_                             |
| **Friendships & Social Life** | Social circles, trust, belonging. <br> _"Why do I feel so isolated from others?"_                   |
| **Spirituality & Purpose**    | Soul path, meaning, karmic lessons. <br> _"What am I meant to learn in this lifetime?"_             |
| **Decisions & Dilemmas**      | Hard choices, forks in the road. <br> _"Should I move or stay?"_                                    |
| **Timing & Future**           | When something will happen. <br> _"When will things improve for me?"_                               |
| **Creativity & Expression**   | Creative work, self-expression. <br> _"Will my art reach others?"_                                  |


### TODO
- [x] Tarot Reading Combinations and Questions
- [x] Snapshots . . . (to be removed...) <-> needs the actual multimodal
- [x] Supabase object handler for handling database during users interaction
    - [x] Validate the user exists. - a unique ID should be assigned to frontend everytime the user installs in a new device and if this is not created, the api rejects and returns errors.
    - [x] Raw decoding output storage / update
    - [x] Decoder Meter combination storage unique to user
    - [ ] Tarot reading with unique id
- [x] Clean up the decoder state
- [x] Define and clean up the (special) Exception Cases
*External Development*
- [x] Lightning Ollama SDK
- [x] Template this package and push to gitlab as its own build
- [x] Setup Lightning studio with ollama SDK and serve the Lightning AI API there

### Long Term Objective
- [ ] Retains and align readings with the users intent.

### Extra / Good-to-have
- [ ] Tarot Quick Search Tool - Definitions etc. if using card's data from open source tool

# Production Checklist

Before deploying into production - this must be built with either:
- **Nginx Proxy** OR
- **AWS Lambda**
OR can just use Lightning AI studio and serve from there

*NOTE: Local hosting is more preferred in the first 3 months.*

Once defining that ensure that authentication is handled appropriately.

### Databases
1. UserIDs
    - Created time
    - User UUID
    - Decoding Kwargs
2. Tarot Readings - main corpus
    - User Inputs
        - Question
        - Card Spread
        - Card Options
    - LLM Raw input
    - LLM Raw output
        - Raw response
        - Response
        - Raw input

3. [Optional] User's analytics
    - Screen time
    - Number of time they use the app
4. [Optional] if the first method doesn't allow extra features stored with defining user ids then make a new database to store the user's IDs
5. General Development Dev Logs -- logging txts

### Data Attribution

- `card_data.json` is derived from [ekelen/tarot-api](https://github.com/ekelen/tarot-api), licensed under the MIT License.
