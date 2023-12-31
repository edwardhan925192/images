import pickle
import os
import sys
import argparse
import numpy as np
import torch
import torch.nn as nn
from tqdm import tqdm
from schedular.scheduler import initialize_scheduler
import json
import pandas as pd
import copy
import torchvision.ops
#from times_config import configs
import matplotlib.pyplot as plt

device = 'cuda' if torch.cuda.is_available() else 'cpu'

def train_model(model, df_train, df_validation, learning_rate, num_epochs, batch_sizes, configs, criterion, scheduler_bool):
    '''
    1. Takes model trainset and validation set
    2. Load Data with datasets
    3. Train (scheduler, criterion, optimizer)
    4. Predict validation set
    '''

    best_val_loss = float('inf')
    best_model_state = None
    best_epoch = -1

    model_type = model

    training_loss_history = []
    validation_loss_history = []

    # ==================== MODEL SELECTION ========================== #
    model = Model(configs).to(device)

    # ==================== CRITERION ========================== #    
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # =================== Scheduler initialization ======================= #
    if scheduler_bool:
      scheduler = initialize_scheduler(optimizer, configs)

    # ==================== TRAINING ========================== #    
    train_dataset = TimeSeriesDataset(output_type, df_train, configs.seq_len, configs.pred_len, target_col)
    train_loader = DataLoader(train_dataset, batch_size=batch_sizes, shuffle=False)

        for epoch in range(num_epochs):
            model.train()
            total_loss = 0

            for batch_idx, (batch_data, batch_target) in enumerate(tqdm(train_loader, desc=f"Epoch {epoch + 1}/{num_epochs}")):
                batch_data, batch_target = batch_data.to(device), batch_target.to(device)
                optimizer.zero_grad()
                outputs = model(batch_data)

                # ============== LOSSES ==================== #
                loss = dice_loss(outputs, batch_target)
                loss.backward()
                optimizer.step()
                total_loss += loss.item()

                # ========== Scheduler ============= #
                if scheduler_bool and configs.scheduler_update_type == 'batch':
                  scheduler.step(epoch + batch_idx / len(train_loader))

            # Update Scheduler after each epoch if specified
            if scheduler_bool and configs.scheduler_update_type == 'epoch':
                scheduler.step()

            average_training_loss = total_loss / len(train_loader)

            # Validation step after each epoch for each validation set
            model.eval()
            total_val_loss = 0

            for val_df in df_validation:
                val_dataset = TimeSeries_ValDataset(output_type, val_df, configs.seq_len, configs.pred_len, target_col, batch_sizes)
                val_loader = DataLoader(val_dataset, batch_size=batch_sizes, shuffle=False)

                val_loss = 0
                with torch.no_grad():
                    for batch_data, batch_target in val_loader:
                        batch_data, batch_target = batch_data.to(device), batch_target.to(device)
                        outputs = model(batch_data)
                        val_loss += loss.item()

                total_val_loss += val_loss / len(val_loader)

            average_validation_loss = total_val_loss / len(df_validation)
            training_loss_history.append(average_training_loss)
            validation_loss_history.append(average_validation_loss)
            print(f"Epoch {epoch + 1}/{num_epochs}, Training Loss: {average_training_loss}, Average Validation Loss: {average_validation_loss}")

            # Update best validation loss and epoch
            if average_validation_loss < best_val_loss:
                best_val_loss = average_validation_loss
                best_epoch = epoch
                print('=================Current_BEST======================')
                best_model_state = copy.deepcopy(model.state_dict())

    print(f"Best Epoch: {best_epoch + 1} with Validation Loss: {best_val_loss}")

    return training_loss_history, validation_loss_history, best_epoch, best_model_state

def test_model(model, test, learning_rate, num_epochs, batch_sizes, configs, criterion, scheduler_bool):
    '''
    Retrain the model with full datasets and make a final prediction
    '''
    model_type = model
    best_model_state = None
    # ==================== MODEL SELECTION ========================== #
    model = Model(configs).to(device)

    # ==================== CRITERION ========================== #
    def dice_loss(pred, target, smooth = 1.):
        pred = pred.contiguous()
        target = target.contiguous()

        intersection = (pred * target).sum(dim=2).sum(dim=2)
        loss = (1 - ((2. * intersection + smooth) / (pred.sum(dim=2).sum(dim=2) + target.sum(dim=2).sum(dim=2) + smooth)))
        return loss.mean()

    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)

    # =================== Scheduler initialization ======================= #
    if scheduler_bool:
      scheduler = initialize_scheduler(optimizer, configs)

    test_dataset = TimeSeries_TestDataset(test, configs.seq_len)
    test_loader = DataLoader(test_dataset, batch_size=batch_sizes, shuffle=False)

    train_dataset = TimeSeriesDataset(output_type, test, configs.seq_len, configs.pred_len, target_col)
    train_loader = DataLoader(train_dataset, batch_size=batch_sizes, shuffle=False)

    for epoch in range(num_epochs):
        model.train()

        for batch_idx, (batch_data, batch_target) in enumerate(tqdm(train_loader, desc=f"Epoch {epoch + 1}/{num_epochs}")):
                batch_data, batch_target = batch_data.to(device), batch_target.to(device)

                optimizer.zero_grad()
                outputs = model(batch_data)

                loss = dice_loss(outputs, batch_target)
                loss.backward()
                optimizer.step()

                # ========== SCHEDULER ========== #
                if configs.scheduler_bool and configs.scheduler_update_type == 'batch':
                  scheduler.step(epoch + batch_idx / len(train_loader))

            # Update Scheduler after each epoch if specified
        if configs.scheduler_bool and configs.scheduler_update_type == 'epoch':
          scheduler.step()

    best_model_state = copy.deepcopy(model.state_dict())
    model.eval()
    predictions = []
    with torch.no_grad():
        for batch_test_data in test_loader:
            batch_test_data = batch_test_data.to(device)
            outputs = model(batch_test_data)

            predictions.extend(outputs.cpu().numpy())

    return predictions,best_model_state
