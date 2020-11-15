#!/bin/bash

for FILE_NAME in input/mongstad/*
do
	export INSTANCE_NAME=$FILE_NAME
	echo "$INSTANCE_NAME"
	python3 -m arc_flow.mathematical_model.arc_flow_model

	sleep 1
done

