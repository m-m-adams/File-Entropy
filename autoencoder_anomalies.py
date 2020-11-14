# %%
import pandas as pd
import numpy as np
import torch
from torch import nn, optim
import matplotlib.pyplot as plt

df = pd.read_csv('./sampledata.csv')
rand = np.random.rand(df.shape[0])
test = rand >= 0.9
val = (rand >= 0.8) & (rand < 0.9)
train = rand < 0.8

train_data = torch.tensor(df[train].iloc[:, 1:].to_numpy().astype(np.float32))
mean = train_data.mean(0)
std = train_data.std(0)
std[std == 0.] = 1
test_data = torch.tensor(df[test].iloc[:, 1:].to_numpy().astype(np.float32))
val_data = torch.tensor(df[val].iloc[:, 1:].to_numpy().astype(np.float32))
train_loader = torch.utils.data.DataLoader(
    train_data, batch_size=128, shuffle=True, num_workers=4, pin_memory=True
)

test_loader = torch.utils.data.DataLoader(
    test_data, batch_size=32, shuffle=False, num_workers=4
)

val_loader = torch.utils.data.DataLoader(
    val_data, batch_size=32, shuffle=False, num_workers=4
)


class AE(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.mean = kwargs["mean"].to(device)
        self.std = kwargs["std"].to(device)
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
        # print(f"original was {features[0,:]}")
        features = (features - self.mean) / self.std
        # print(f"scaled to {features[0,:]}")
        activation = torch.relu(self.encoder_hidden_layer(features))
        activation = torch.relu(self.encoder_hidden_layer2(activation))
        code = torch.relu(self.encoder_output_layer(activation))
        activation = torch.relu(self.decoder_hidden_layer(code))
        activation = torch.relu(self.decoder_hidden_layer2(activation))
        reconstructed = torch.relu(self.decoder_output_layer(activation))
        return reconstructed


#  use gpu if available
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

model = AE(mean=mean, std=std, input_shape=64).to(device)

# create an optimizer object
# Adam optimizer with learning rate 1e-3
optimizer = optim.Adam(model.parameters(), lr=1e-2)

# mean-squared error loss
criterion = nn.MSELoss()
epochs = 50
for epoch in range(epochs):
    trainloss = 0
    for batch_features in train_loader:
        # reshape mini-batch data to [N, 64] matrix
        batch_features = batch_features.view(-1, 64).to(device)

        optimizer.zero_grad()

        # compute reconstructions
        outputs = model(batch_features)

        # compute training reconstruction loss
        loss = criterion(outputs, batch_features)

        # compute accumulated gradients
        loss.backward()

        # perform parameter update based on current gradients
        optimizer.step()

        # add the mini-batch training loss to epoch loss
        trainloss += loss.item()
    # compute the epoch training loss
    trainloss = trainloss / len(train_loader)
    valloss = 0
    for batch_features in val_loader:
        batch_features = batch_features.view(-1, 64).to(device)
        outputs = model(batch_features)
        loss = criterion(outputs, batch_features)
        valloss += loss.item()
    valloss = valloss / len(val_loader)
    # display the epoch training loss
    print(f"epoch : {epoch + 1}/{epochs}, loss = {trainloss:.6f}, val loss = {valloss:.6f}")

rand_test = np.zeros((1000, 64), np.float32)
for i in range(rand_test.shape[0]):
    matrix = np.random.rand(8, 8)
    matrix /= matrix.sum(axis=1)[:, None]
    rand_test[i, :] = matrix.ravel()

rand_test = torch.tensor(rand_test)
rec = model(rand_test.to(device))
error = criterion(rec, rand_test.to(device))
print(f'error on random data is {error:.6f}')

testloss = 0
for batch_features in test_loader:
    batch_features = batch_features.view(-1, 64).to(device)
    outputs = model(batch_features)
    loss = criterion(outputs, batch_features)
    testloss += loss.item()
testloss = testloss / len(val_loader)
print(f'error on test data is {testloss:.6f}')

# %%

nplot = 10
fig, axs = plt.subplots(2, nplot, figsize=(20,4))

for i in range(nplot):
    feat = torch.tensor(df.iloc[i, 1:].to_numpy().astype(np.float32))
    output = model(feat)

    orig = feat.detach().numpy().reshape(8, 8)
    out = output.detach().numpy().reshape(8, 8)
    axs[0, i].imshow(orig)
    axs[1, i].imshow(out)
    axs[0, i].axis('off')
    axs[1, i].axis('off')
fig.tight_layout()
plt.show()
