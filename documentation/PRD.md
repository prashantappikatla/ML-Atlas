⸻

Product Requirements Document

Project: Machine Learning Atlas & Lab Platform

⸻

1. Overview

Product Name

Machine Learning Atlas

Product Vision

Machine Learning Atlas is a technical learning and experimentation platform designed to document, explore, and implement machine learning algorithms.

The platform will contain:
	•	Structured documentation of ML algorithms
	•	Standardized metadata and research notes
	•	Interactive lab environments for experimentation
	•	Educational explanations and practical implementations

The project serves two purposes:
	1.	Personal knowledge system for deep ML study
	2.	Public portfolio platform demonstrating technical ML expertise

⸻

2. Objectives

Primary Goals
	1.	Create a comprehensive database of machine learning algorithms
	2.	Document algorithm theory, parameters, and use cases
	3.	Provide interactive labs demonstrating each algorithm
	4.	Build a structured, searchable ML reference platform
	5.	Maintain progress tracking for learning and implementation

⸻

3. Target Users

Primary User

The platform creator (personal research and learning).

Secondary Users

External developers, researchers, or students who want:
	•	ML algorithm reference material
	•	working algorithm implementations
	•	educational labs

⸻

4. Core Features

4.1 Algorithm Documentation

Each algorithm will have a structured page containing:

Overview
	•	algorithm description
	•	historical background
	•	original research paper

Technical Details

Sections include:
	•	mathematical intuition
	•	algorithm workflow
	•	training process
	•	computational complexity

Parameters

List all configurable parameters:

Example

Parameter	Description	Default



⸻

Compatibility Matrix

Data Type	Compatibility
Tabular	Yes
Images	No
Text	Partial


⸻

Strengths and Weaknesses

⸻

Use Cases

Example domains:
	•	finance
	•	healthcare
	•	computer vision
	•	NLP

⸻

Implementation

Each algorithm should include:
	1.	Conceptual explanation
	2.	From-scratch implementation
	3.	Library implementation

Examples:

Python
Scikit-learn
PyTorch
TensorFlow


⸻

Lab

Each algorithm will link to an interactive lab.

Lab types:
	•	visualization
	•	parameter tuning
	•	dataset experiment
	•	model training demo

Labs will run in Streamlit or Gradio apps.

⸻

5. System Architecture

The system consists of four major layers.

⸻

5.1 Frontend Layer

Technology

NextJS (App Router)

Content Format

MDX

Purpose:
	•	algorithm documentation
	•	research notes
	•	diagrams
	•	embedded lab links

Responsibilities

Frontend will provide:
	•	algorithm pages
	•	category browsing
	•	search
	•	filtering
	•	lab launch interface

⸻

Example Pages

/algorithms
/algorithms/supervised
/algorithms/supervised/random-forest
/algorithms/unsupervised/kmeans
/labs
/labs/random-forest-demo


⸻

5.2 Backend Layer

Technology

Python + FastAPI

Purpose

Acts as the main service layer connecting:
	•	database
	•	labs
	•	frontend

⸻

Backend Responsibilities
	•	API for algorithm metadata
	•	lab registry
	•	dataset metadata
	•	progress tracking
	•	search endpoints

⸻

Example API Routes

GET /algorithms
GET /algorithms/{id}

GET /categories

GET /labs
GET /labs/{algorithm}

POST /notes
GET /notes


⸻

5.3 Lab Environment

Labs will run as independent microservices.

Each lab will be implemented using:
	•	Streamlit
or
	•	Gradio

Purpose:
	•	parameter exploration
	•	dataset experimentation
	•	algorithm visualization

⸻

Example Lab Structure

labs/

  kmeans_lab/
      app.py
      dataset_loader.py
      visualization.py

  svm_lab/
      app.py
      demo_data.py


⸻

Example Lab Behavior

User selects:

clusters = 3
dataset = iris

Lab returns:
	•	clustering visualization
	•	metrics
	•	decision boundaries

⸻

5.4 Database Layer

Technology

Supabase Postgres

ORM

SQLModel

⸻

6. Database Schema

⸻

Table: algorithms

id
name
category
subcategory
year
paper_reference
complexity
best_use_case
description
compatibility_tabular
compatibility_image
compatibility_text
compatibility_graph


⸻

Table: algorithm_parameters

id
algorithm_id
parameter_name
description
default_value
parameter_type


⸻

Table: algorithm_notes

id
algorithm_id
note_type
content
created_at


⸻

Table: labs

id
algorithm_id
lab_name
lab_type
url
framework

Example frameworks:

streamlit
gradio


⸻

Table: implementation_status

Tracks personal learning progress.

id
algorithm_id
implemented_from_scratch
implemented_library
lab_created
documentation_complete


⸻

7. Repository Structure

ml-atlas/

frontend/
  nextjs-site/

backend/
  fastapi-server/

labs/
  streamlit/
  gradio/

database/
  models/
  migrations/

content/
  algorithms/
  categories/

notebooks/
  experiments/

datasets/


⸻

8. Content Structure

Algorithm pages stored in MDX:

content/algorithms/supervised/random-forest.mdx

Example structure:

# Random Forest

## Overview

## History

## Mathematical Intuition

## Algorithm Steps

## Parameters

## Strengths

## Weaknesses

## Use Cases

## Implementations

## Lab


⸻

9. Algorithm Categories

Initial categories include:

Supervised Learning
	•	regression
	•	classification
	•	ranking

⸻

Unsupervised Learning
	•	clustering
	•	dimensionality reduction
	•	anomaly detection

⸻

Probabilistic Models
	•	Bayesian networks
	•	HMM
	•	Kalman filters

⸻

Time Series
	•	ARIMA
	•	VAR
	•	GARCH
	•	Prophet

⸻

Deep Learning
	•	CNN
	•	RNN
	•	Transformers

⸻

Generative Models
	•	GAN
	•	VAE
	•	Diffusion

⸻

Reinforcement Learning
	•	Q-learning
	•	PPO
	•	SAC

⸻

Graph Machine Learning
	•	GNN
	•	node embeddings

⸻

Meta Learning
	•	NAS
	•	MAML

⸻

10. Search & Filtering

Users should be able to filter algorithms by:
	•	category
	•	data type
	•	complexity
	•	year
	•	implementation status

⸻

11. Version Control

All code will be stored in a Git repository.

Components tracked:
	•	MDX documentation
	•	Python implementations
	•	lab apps
	•	backend APIs

⸻

12. Phase Roadmap

⸻

Phase 1 — Foundation

Goal:

Create the core platform.

Deliverables:
	•	NextJS site
	•	FastAPI backend
	•	Supabase database
	•	SQLModel schema
	•	initial algorithm pages

⸻

Phase 2 — Algorithm Documentation

Add:
	•	30–50 algorithms
	•	parameter documentation
	•	theoretical explanations

⸻

Phase 3 — Lab Integration

Add:
	•	Streamlit labs
	•	Gradio demos
	•	dataset visualizations

⸻

Phase 4 — Advanced Features

Possible future additions:
	•	vector search
	•	algorithm comparison tools
	•	experiment tracking
	•	AI assistant for algorithm explanations

⸻

13. Success Criteria

The project will be successful if:
	•	100+ ML algorithms documented
	•	50+ implementations completed
	•	30+ interactive labs created
	•	the platform becomes a reference for ML study

⸻

14. Future Expansion

Possible future expansions include:
	•	ML certification study platform
	•	algorithm benchmarking
	•	dataset exploration tools
	•	AI-powered tutoring for algorithms

⸻

15. Guiding Principle

The platform should prioritize:

clarity, experimentation, and deep learning of machine learning concepts.

⸻
