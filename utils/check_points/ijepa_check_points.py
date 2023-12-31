def load_checkpoint(
    device,
    r_path,
    x_encoder,
    predictor,
    y_encoder,
    x_optimizer,
    pred_optimizer

):
    try:
      # -- saved dir
      checkpoint = torch.load(r_path, map_location=torch.device('cpu'))
      epoch = checkpoint['epoch']

      # -- loading x_encoder
      pretrained_dict = checkpoint['x_encoder']
      x_encoder.load_state_dict(pretrained_dict)

      # -- loading predictor
      pretrained_dict = checkpoint['predictor']
      predictor.load_state_dict(pretrained_dict)

      # -- loading y_encoder
      if y_encoder is not None:
          print(list(checkpoint.keys()))
          pretrained_dict = checkpoint['y_encoder']
          y_encoder.load_state_dict(pretrained_dict)

      # -- loading optimizer
      pred_optimizer.load_state_dict(checkpoint['pred_opt'])
      x_optimizer.load_state_dict(checkpoint['x_opt'])

    except Exception as e:
      epoch = 0

    return x_encoder, predictor, y_encoder, x_optimizer, pred_optimizer,  epoch


def save_checkpoint(epoch, checkpoint_freq, base_directory='/content/drive/MyDrive/data/ijepa weights'):

    # Latest checkpoint path
    latest_path = os.path.join(base_directory, '-latest.pth')

    # Save dictionary
    save_dict = {
        'x_encoder': x_encoder.state_dict(),
        'y_encoder': y_encoder.state_dict(),
        'predictor': predictor.state_dict(),
        'x_opt': x_optimizer.state_dict(),
        'pred_opt': pred_optimizer.state_dict(),
        'scaler': None if scaler is None else scaler.state_dict(),
        'epoch': epoch
    }

    # -- Always update the latest checkpoint
    torch.save(save_dict, latest_path)

    # -- Checkpoint frequency updates
    if (epoch + 1) % checkpoint_freq == 0:

        # -- Checkpoint path for specific epoch
        checkpoint_path = os.path.join(base_directory, f'-ep{epoch + 1}.pth')
        torch.save(save_dict, checkpoint_path)
