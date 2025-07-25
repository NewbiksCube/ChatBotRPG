# ChatBot RPG (Early Preview Release)
ChatBot RPG is a new approach to text-based interactive fiction, putting the "G" in "RPG" and moving past simple roleplay chats with personas. Build whole games and scenarios in which the AI operates within a framework of rules, enabling complex quest stage tracking, dynamic events, real inventory, and emergent storytelling with a consistency that is not possible with a chat bot and some memory tricks alone. The goal of this project is to unlock a multitude of new kinds of play styles around the LLM chat medium, from simple branched-narrative games to sandboxing in entirely new open worlds with whole parties of companions.


**Why?**

We've all had a couple of years to explore it - going back and forth with a chat bot set up to roleplay as some kind of interesting or beloved persona, prompting a 'text adventure' with suggested next actions, and have pinged off of an AI to discuss worldbuilding and discover their depth as a storytelling aid. It is very clear that the large language model, inherently predisposed and even designed to adopt and simulate some kind of role, has enormous potential in the area of roleplaying games. In many ways they even solve some of the issues with human-only games, such as scheduling, group availability, turn pacing, GM burnout, and content preference (although we also want to preserve and boost its capacity to tell **our** human stories and ideas and lore, not its own memorized cliches and "isms").

Just like in human storytelling, all of this pent up potential can be lost when given only its own devices to manage and deliver the content (which is why we have storytelling frameworks, like tabletop games). Limitations such as context length, keeping accurate score of mechanics or variables, and strong internal biases and repetition can quickly ruin the experience, reducing a chatbot's capacity to roleplay into something more like a dream than a coherent and whole experience.
Take, for example, trying to roleplay with a chatbot inside your own fantasy world:

- In the majority of cases, the first female NPC you meet will always be named Elara
- In most cases the first far-off land you hear of will be Eldoria
- If you prompt it that one of your three adventuring companions is named Sally, she very well might turn into Elara, the Elven princess-warrior several pages later
- It will struggle to adhere to your own lore at any meaningful depth and insert its own cliches
- If you leave a certain setting in the narrative and come back later, that setting will be different
- Weather patterns might have difficulty changing
- Once a character starts talking to you, they might have difficulty stopping or leaving
- Characters introduced later in a scene might assume they know the names of characters referenced previously in the scene, even if they've never met
- What is narrated as an internal experience to your character or an NPC may become referenced by other characters the next turn in their dialogue
- Among many, many other immersion-breaking cliches, inconsistencies, and hallucinations

Let's move beyond this, and give AI the actual capacity to run campaign-level games and tell consistent, epic stories.

**How do we fix it?**

To aid in the construction of RPGs, this toolkit provides a number of modules that are inspired by current existing RPG creation kits and allow creators to build their own games and systems, without needing to have any coding experience. These are:

- **Settings/Worlds**: Build interconnected settings with as nodes on actual maps, link them together with paths that have travel times between their settings, and overlay regions and features to allow dynamic descriptions of these locations in game
- **Time Passage**: Sync your game to your computer clock or simulate the passage of its own time, allowing for dynamic pacing, changing world events, day/night cycles, and more
- **Character Management**: Design NPCs with variables/status, equipment, backstories, starting locations, and real schedules that allow them to move around the world
- **Rules Engine**: The core of the engine - create powerful conditional logic that executes on timers or on each turn, which follows an "if-then-else" format
- **Keywords Matching**: Insert context when various names or keywords are used. Excellent for the recognition of names or phrases in your world lore
- **Inventory System**: Full RPG inventory management for players and NPCs
- **Random Lists**: Preset, generate, and use weighted random lists to help eliminate bias, such as the infamous "Elara" bias
- **Scribe**: An in-built AI agent specifically for the purpose of scaling up the game-building process. Leverage its help for worldbuilding, writing rule files for your game automatically, generating character files for your game automatically, or just explaining the interface and UI to you.

This is currently an initial preview for developers, game masters, and tech enthusiasts. There are no fully playable games yet or any plug-and-play experiences for the casual roleplayer or gamer. Full implementation of these creation modules is nearing completion, and about 80%-90% of the features are now explorable. If you enjoy game design and worldbuilding, there should be enough there to help you begin forming large swaths of your game world and logic, while the rest of the features are completed in the near term, so despite it being a bit rough around the edges, feel free to start building serious stuff now and the engine will catch up to you.

## Getting Started

1. **Download files to a virtual environment or folder somewhere.**
2. **Add your OpenRouter API key to `config.json.` More LLM services will be supported soon.**
3. **Ensure that Python is installed.**
4. **Unzip the contents of `Demo.zip` into the main folder (this contains the actual demo "game").**
5. **Run `START.bat`**

## Documentation

- **Coming Soon**

## Anticipated FAQ:

**Q: How do I access the game building tools?**

A: There is a small splitter handle to the left of the chat screen. Drag it open (to the right) to open the tool bar.

**Q: How is a game represented?**

A: A game is represented by certain files and folders inside the /data/ directory (example, /data/My RPG/various files and folders). While other approaches to data persistence might be explored in the future, game data is currently stored as various .json files within various subfolders (the game engine will organize this on its own). Game state is primarily maintained by these files. Saves are currently just duplicate folders containing exact copies or snapshots of a game state at the time it was saved and kept in a /saves/ folder (Loading a save just restores this to the main state). If you are using map images, .jpg or other image formats can also be stored in there.

**Q: What inference services can I use?**

A: This was developed with OpenRouter.ai, but you can also run it locally. There is also support for Google GenAI. Mre services are coming soon.

**Q: Which model should I use?**

A: My favorite one that sits at the most optimal place regarding functionality/reasoning, and cost per inference, is the Gemini 2.5 Flash Lite Preview. However, most models that understand basic reasoning and classification will do. Do not use "thinking" models - this project might not account for "thinking" tokens correctly in all cases, and is already designed to allow game designers to funnel the AI down its own "thinking" trees of thought that are more closely aligned to the goals of their game mechanics. Do not use models that are predisposed towards long, flowery text such as creative writing models (following instructions directly without adding extra stuff is going to be the number one priority).

**Q: Can I run this locally?**

A: Maybe, I haven't tested this and support for it is coming soon. I must emphasize the importance of reasoning, instructions-following, and probably newer models, when picking which model to run the game. Locally hosted models tend to be smaller, and smaller models often do not reason very well. Very often, reasoning skills are a bit of a trade-off with the creative writing models, so the creative writing or RP-based models are not going to be nearly as useful here (counter-intuitive as it may sound) as something that can classify things with a little bit of common sense, and follow instructions reasonably well. You might also want about 32k or more token context window.

**Q: What are you using for UI? Why no browser-based or website?**

A: Currently PyQt5, as LLMs themselves are pretty familiar with it and I preferred a standalone experience I could do to my exact vision. One of the design choices I made early on is keeping dependencies and the install process relatively straightforward and I wanted it to run with just Python. If the demand is there, then I may explore other UI choices or browser-based things in the future.

**Q: Why is it all in only one color?**

A: Doing the UI from scratch purely by vision was complicated, and iterating through all the little pieces to set up different visual themes, and then deciding on all that to show off the stylization conventions was just too much off-priority work for right now. While UI styling may improve in the future, for now, I'm focused on the game engine and my own game contents instead, so the monochrome CRT style kept it very uniform for me. Plus, it looks kind of like some of the first text adventures like Zork, and everyone has a favorite color (I think), so this should do for now.

**Q: Why is it shimmering?**

A: It's like an old CRT monitor. This is a pretty common visual trope with cyberpunk or sci fi type computer terminals and it kind of fits the first theme I was looking for. If it bothers you then you can disable or adjust it in the options menu but I think it's kind of cool.

**Q: Sprites? Pictures? Tilesets?**

A: No. This engine is not intended to render that kind of game. For visual material, maps are supported and encouraged, and there may be some limited support for character portraits or images in the future. However, it is my expectation that as AI, VR, and other cool stuff continues to develop, future technologies will already become capable of rendering visual scenes from text. I would also like to reserve future space for the idea of getting to play using only voice input/output. For these reasons I like to consider that ChatBot RPG does "computer games," but it does not do "video games." There are however some basic screen effects and sound effects that can optionally be used.

**Q: Music? Sound effects?**

A: Yes, support for this is planned in the near future. UI has some basic sound effects with more planned in the future.

**Q: I started this through my dev console and the output says (this/that/error etc). Should I be concerned?**

A: No. Ignore all the console output, that is only for me at this time.

**Q: It's hard to talk RPG without talking combat, or at least conflict.  Is there a combat system, conflict resolution, player or NPC death? Consequences?**

A: The tools should exist for game makers to create their own combat or conflict-resolution systems. One will certainly be in place for the world/game I am building. Game creators can use the "Game Over" trigger action in the Rules system to force an end to the current game session and reset the player to the starting screen.

**Q: Multiplayer??**

A: Possibly, especially if I got a lot of technical help and a strong demand for it, but it's not a current priority. I'm not opposed to the idea and I do one day want to be able to play with some friends, but a completed single player experience for things is my first priority. However, given how quickly material can be built within this engine, there is probably a big opportunity right away for collaborative worldbuilding (sort of like Skyrim mods). This is the main communal experience I'm looking forward to, if this project generates any interest.

**Q: Why can't I select text and copy/paste to/from the chat? Why can't I redo post? Why do I have to write like (3rd person, full sentences, etc)?**

A: While people can make any games they want, the type of game this is intended to help create are those that can exercise some kind of faculties of the player. Not being able to just rewrite things (beyond the save/load functions), having timed elements rather than strict turn-based order, and solid in-game consequences for decisions will all put a strong emphasis on making sound decisions in a timely fashion, while sometimes under pressure. This more game-like experience is what I'm aiming for, so the project will lean more in that direction and less in the experimental chatbot direction.

**Q: But, what if the AI makes a mistake? Wont the randomness make a game-like environment impossible?**

A: Most of the elements of a scene can be programatically tracked (or randomized properly), and broken into very small moving parts that are easily tracked and handled by modern LLMs. Strong state-tracking pipelines, clear prompting, and later models vs. earlier models can all come together in a manner that make such mistakes very rare. The goal of this project is to finally provide the tools needed to properly and comprehensively rein in the chaos that often defines LLM use (at least in the context of text adventure). At the end of the day this is mainly a prompt-engineering toolkit, and that's a skillset that's still being explored, but what's consistently kept me developing this project is actually the success rate I've experienced from strong prompt engineering. The one thing that might convince me to stop working on this has always been some barrier that proves impossible to overcome, but so far, each element that an RPG engine needs has, through trial and error, been successfully prototyped in my journey and I just haven't hit that limit yet.

**Q: Why is the map editor so CPU heavy?**

A: I do plan to prioritize optimizations in the future - but for now, just getting it working at all was a really huge task for me.

## Known Issues

- Small window popup on game switch or loading.
- Windows might twitch or adjust upon receiving some chat messages and other events. This is being worked on.
- The window dimensions are not collapsible to as small as I want, yet, and may have inconsistencies or issues on some smaller resolution devices.
- Some UI elements might be a bit cluttered to provide a smooth experience, but it was the best I could do for now.
- Some bugs may occur during the creation of settings if a certain order of operations are not followed.
- Changing games causes a visual UI artifact if the main window is rescaled after the switch. Restarting the app fixes this problem.
- Changing colors doesn't cause all UI elements to change right away. Restarting will fix this issue.
- The mouse cursor is wrong or doesn't interact with some GUI elements correctly. A fix for this is coming soon.

## Acknowledgments

Built with passion for the emerging intersection of AI technology and interactive fiction. Special thanks to the LLM RPG communities SillyTavern (especially Veritasr and the LLM World Engine thread) and Tenebrous Tales Interactive for inspiration and feedback.

## License

This project is licensed under the GNU General Public License v3.0.

## Community

A place to talk about it: https://discord.gg/bwpYhcVs
