import pandas as pd
import numpy as np
import torch
from torch import nn, optim
import matplotlib.pyplot as plt

df = pd.read_csv('./Entropyvis-malware-classification/windowslegitexes.csv')
rand = np.random.rand(df.shape[0])
test = rand>=0.9
val = (rand >= 0.8) & (rand <0.9) 
train = rand < 0.8

train_data = torch.tensor(df[train].iloc[:,1:].to_numpy().astype(np.float32))
mean = train_data.mean()
std = train_data.std()
test_data = torch.tensor(df[test].iloc[:,1:].to_numpy().astype(np.float32))
val_data = torch.tensor(df[val].iloc[:,1:].to_numpy().astype(np.float32))
train_loader = torch.utils.data.DataLoader(
    train_data, batch_size=128, shuffle=True, num_workers=4, pin_memory=True
)

test_loader = torch.utils.data.DataLoader(
    test_data, batch_size=32, shuffle=False, num_workers=4
)

class AE(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.mean = kwargs["mean"]
        self.std = kwargs["std"]
        self.encoder_hidden_layer = nn.Linear(
            in_features=kwargs["input_shape"], out_features=32
        )
        self.encoder_hidden_layer2 = nn.Linear(
            in_features=32, out_features=16
        )
        self.encoder_output_layer = nn.Linear(
            in_features=16, out_features=8
        )
        self.decoder_hidden_layer = nn.Linear(
            in_features=8, out_features=16
        )
        self.decoder_hidden_layer2 = nn.Linear(
            in_features=16, out_features=32
        )
        self.decoder_output_layer = nn.Linear(
            in_features=32, out_features=kwargs["input_shape"]
        )

    def forward(self, features):
        features = (features-self.mean)/self.std
        activation = torch.relu(self.encoder_hidden_layer(features))
        activation = torch.relu(self.encoder_hidden_layer2(activation))
        code = torch.relu(self.encoder_output_layer(activation))
        activation = torch.relu(self.decoder_hidden_layer(code))
        activation = torch.relu(self.decoder_hidden_layer2(activation))
        reconstructed = torch.relu(self.decoder_output_layer(activation))
        return reconstructed
#  use gpu if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# create a model from `AE` autoencoder class
# load it to the specified device, either gpu or cpu
model = AE(mean=mean, std=std, input_shape=64).to(device)

# create an optimizer object
# Adam optimizer with learning rate 1e-3
optimizer = optim.Adam(model.parameters(), lr=1e-2)

# mean-squared error loss
criterion = nn.MSELoss()
epochs = 20
for epoch in range(epochs):
    loss = 0
    for batch_features in train_loader:
        # reshape mini-batch data to [N, 64] matrix
        # load it to the active device
        batch_features = batch_features.view(-1, 64).to(device)
        
        # reset the gradients back to zero
        # PyTorch accumulates gradients on subsequent backward passes
        optimizer.zero_grad()
        
        # compute reconstructions
        outputs = model(batch_features)
        
        # compute training reconstruction loss
        train_loss = criterion(outputs, batch_features)
        
        # compute accumulated gradients
        train_loss.backward()
        
        # perform parameter update based on current gradients
        optimizer.step()
        
        # add the mini-batch training loss to epoch loss
        loss += train_loss.item()
    
    # compute the epoch training loss
    loss = loss / len(train_loader)
    valout = model(val_data)
    valloss = criterion(valout, val_data)
    # display the epoch training loss
    print("epoch : {}/{}, loss = {:.6f}, val loss = {:.6f}".format(epoch + 1, epochs, loss, valloss))

rand_test = np.zeros((1000,64), np.float32)
for i in range(rand_test.shape[0]):
  matrix = np.random.rand(8,8)
  matrix /= matrix.sum(axis=1)[:,None]
  rand_test[i, :] = matrix.ravel()
rand_test = torch.tensor(rand_test)
rec = model(rand_test)
error = criterion(rec, rand_test)
print(f'error on random data is {error:.6f}')


test_test = torch.tensor(rand_test)
rec = model(test_loader)
error = criterion(rec, test_test)
print(f'error on random data is {error:.6f}')



nplot=10
fig, axs = plt.subplots(2, 10)

for i in range(nplot):
  input = torch.tensor(df.iloc[i,1:].to_numpy().astype(np.float32))
  output = model(input)

  orig = input.detach().numpy().reshape(8,8)
  out = output.detach().numpy().reshape(8,8)
  axs[0,i].imshow(orig)
  axs[1,i].imshow(out)
fig.tight_layout()
plt.show()
