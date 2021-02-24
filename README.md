# Flappy Bird AI
**Full-length descriptions** and **visual demonstration** of the project: https://www.wontaejungportfolio.com/mywork

A repository containing an implementation of the game, "Flappy Bird", and an AI that perfects the game using neural networks.

Language: Python  
Libraries: pygame, neat, os, random

## Intro

"Flappy Bird" is a side-scrolling game released in 2013, where the player controls a bird, and attempts to fly between green pipes without hitting them.

Despite its simplistic mechanic and design, the game is renown for its high level of difficulty, and addictiveness.

In this project, I recreated "Flappy Bird", and developed an AI algorithm that learns how to progress through the game endlessly, utilizing neural networks.

## /

**config-feedforward.txt:**  
The feedforward specifications, for utilizing the NEAT algorithm

**config_explanations.txt:**  
A copy of config-feedforward.txt, but with explanations of each parameter, and its functionality

**FBIRD.py:**  
The main algorithm (Game, and neural network implementations)

## Outcome:
"Perfect bird" achieved in max. 4 generations, each generation with population size 20. Resulting bird survived 48 hours without collision

## Reference:
https://github.com/techwithtim/NEAT-Flappy-Bird
