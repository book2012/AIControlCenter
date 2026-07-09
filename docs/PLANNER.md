# Planner

## Status

✅ PlannerAgent
✅ Planner API
✅ Telegram /plan
✅ PlanStore
✅ Plan Review

## Purpose

Planner converts user goals into draft execution plans.

## API

POST /planner/plan
GET /planner/plans
GET /planner/plans/{plan_id}
POST /planner/plans/{plan_id}/review

## Command

/plan <goal>

## Safety

Planner creates plans only.
It does not execute actions.
