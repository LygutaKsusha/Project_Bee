#!/usr/bin/env python3
# @file TrainNetwork.py
#
# @brief This file is used to train the BeeModel which is used

import BeeModel

MODEL_SAVE_PATH = "SavedModel"

import tensorflow_datasets as tfds
train, val = tfds.load('bee_dataset/bee_dataset_150',
    batch_size=11,
    as_supervised=True,
    split=["train[0%:50%]", "train[50%:100%]"])


model = BeeModel.get_bee_model(150, 75)
model.fit(
        train,
        validation_data=val,
        epochs=20,
        verbose=1,
        callbacks=[]
    )

# Save the model and show the summary
model.save(MODEL_SAVE_PATH)
model.summary()
