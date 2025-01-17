# %%
import pandas as pd
import numpy as np
import torch
import tqdm
import ast
from torch import nn, optim
from scipy import stats
import matplotlib.pyplot as plt
import torch.nn.functional as F
# %%


def process_image(x):
    x = np.array(x)
    x[0, 0] = 0
    x = 32**2*x/x.sum()
    return x


df = pd.read_csv('./data/sampledata.csv')
df['name'] = df['name'].str.strip('[]').str.split().str[-1].str.split("\\").str[-1].str.strip("'")
df.image = df.image.apply(lambda x: ast.literal_eval(x))
df = df[df.image.apply(len) == 32]
df.image = df.image.apply(process_image)

maldf = pd.read_csv('./data/labelledVTEntropy2.csv').dropna()
maldf.insert(0, 'cat', maldf['detectedname'].str.split(':|\.').str[0])
desired = ['Virus', 'Trojan']
maldf = maldf[maldf.cat.isin(desired)]
maldf.image = maldf.image.apply(lambda x: ast.literal_eval(x))
maldf.image = maldf.image.apply(process_image)

# %%
goodrand = np.random.rand(df.shape[0])
test = goodrand >= 0.9
val = (goodrand >= 0.8) & (goodrand < 0.9)
train = goodrand < 0.8

malrand = np.random.rand(maldf.shape[0])
valmal = maldf[malrand < 0.8]
testmal = maldf[malrand >= 0.8]

traindf = df[train]
testdf = df[test]
valdf = df[val]
size = 32

train_data = torch.tensor(np.array([np.array(xi) for xi in df.image]).astype(np.float32)).view(-1, 1, size, size)
test_data = torch.tensor(np.array([np.array(xi) for xi in df.image]).astype(np.float32)).view(-1, 1, size, size)
val_data = torch.tensor(np.array([np.array(xi) for xi in df.image]).astype(np.float32)).view(-1, 1, size, size)
mal_val_data = torch.tensor(np.array([np.array(xi) for xi in maldf.image]).astype(np.float32)).view(-1, 1, size, size)
mal_test_data = torch.tensor(np.array([np.array(xi) for xi in maldf.image]).astype(np.float32)).view(-1, 1, size, size)

# %%
params = {
    'batch_size': 256, 'shuffle': True, 'num_workers': 4, 'pin_memory': True
}
train_loader = torch.utils.data.DataLoader(train_data, **params)

test_loader = torch.utils.data.DataLoader(test_data, **params)

val_loader = torch.utils.data.DataLoader(val_data, **params)

mal_val_loader = torch.utils.data.DataLoader(mal_val_data, **params)

mal_test_loader = torch.utils.data.DataLoader(mal_test_data, **params)
# %%


def squareloss(x, x_hat):
    error = torch.square(x-x_hat).mean(1)
    return error


class AE(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.mean = kwargs["mean"].to(device)
        self.std = kwargs["std"].to(device)
        self.encoder_hidden_layer = nn.Linear(
            in_features=64, out_features=32
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
            in_features=32, out_features=64
        )

    def forward(self, features):
        # print(f"original was {features[0,:]}")
        features = (features - self.mean) / self.std
        features = features.reshape(-1,64)
        
        # print(f"scaled to {features[0,:]}")
        activation = F.relu(self.encoder_hidden_layer(features))
        activation = F.relu(self.encoder_hidden_layer2(activation))
        code = F.relu(self.encoder_output_layer(activation))
        activation = F.relu(self.decoder_hidden_layer(code))
        activation = F.relu(self.decoder_hidden_layer2(activation))
        reconstructed = F.relu(self.decoder_output_layer(activation))
        return reconstructed.reshape(-1,1,8,8)*self.std +self.mean


class ConvAE(nn.Module):
    def __init__(self, **kwargs):
        super().__init__()
        self.conv1 = nn.Conv2d(1, 16, 10, padding=1)
        self.pool = nn.MaxPool2d(2, 2)
        self.conv2 = nn.Conv2d(16, 4, 5, padding=1)

        self.t_conv1 = nn.ConvTranspose2d(4, 16, 3, stride=1)
        self.t_conv2 = nn.ConvTranspose2d(16, 1, 8, stride=1)

    def forward(self, x):

        x = F.relu(self.conv1(x))

        x = F.relu(self.conv2(x))

        x = F.relu(self.t_conv1(x))

        x = self.t_conv2(x)

        return x


def computeloss(mod, load, crit):
    valloss = 0
    for batch_features in load:
        batch_features = batch_features.to(device)
        outputs = mod(batch_features)
        loss = crit(outputs, batch_features)
        valloss += loss.item()
    valloss = valloss / len(load)
    return valloss


# device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
device = torch.device("cuda")


model = ConvAE().to(device)

optimizer = optim.Adam(model.parameters(), lr=1e-3)
scheduler = optim.lr_scheduler.StepLR(optimizer, 50, 0.5)
# mean-squared error loss
criterion = nn.MSELoss()
epochs = 200
val = []
train = []
mal = []
with tqdm.tqdm(total=epochs) as epoch_pbar:
    for epoch in range(epochs):
        trainloss = 0
        for batch_features in train_loader:
            # reshape mini-batch data to [N, 64] matrix
            batch_features = batch_features.to(device)

            optimizer.zero_grad()

            # compute reconstructions
            outputs = model(batch_features)

            # compute training reconstruction loss
            loss = criterion(outputs, batch_features)

            # compute accumulated gradients
            loss.backward()

            # perform parameter update based on current gradients
            optimizer.step()
            scheduler.step(loss)

            # add the mini-batch training loss to epoch loss
            trainloss += loss.item()
        # compute the epoch training loss
        trainloss = trainloss / len(train_loader)
        train.append(trainloss)
        val.append(computeloss(model, val_loader, criterion))
        mal.append(computeloss(model, mal_val_loader, criterion))
        # display the epoch training loss
        # print(f"epoch : {epoch + 1}/{epochs}, loss = {trainloss:.6f}, val loss = {valloss:.6f}")
        epoch_pbar.update()
plt.plot(val, label='validation')
plt.plot(train, label='training')
plt.plot(mal, label='malware')
plt.legend()
plt.yscale("log")
plt.show()
# %%


def plot_images(data, nplot, label, title):
    fig, axs = plt.subplots(2, nplot, figsize=(20, 4))
    for i in range(nplot):
        feat = torch.tensor(np.array([np.array(xi) for xi in data.iloc[i].image]).astype(np.float32)).view(-1, 1, 32,32).to(device)
        output = model(feat)

        orig = feat.detach().cpu().numpy().reshape(32, 32)
        out = output.detach().cpu().numpy().reshape(32, 32)

        error = np.square(orig-out).mean()
        axs[0, i].imshow(orig)
        axs[1, i].imshow(out)
        axs[0, i].axis('off')
        axs[1, i].axis('off')
        axs[0, i].set_title(data.iloc[i][label].split("/")[-1])
        axs[1, i].set_title(f'e = {error: .3f}')

    fig.suptitle(title, fontsize=16)
    fig.subplots_adjust(top=0.88)
    plt.show()


plot_images(df, 10, 'name', 'legitimate')
plot_images(maldf, 10, 'detectedname', 'malicious')

# %%
print('determining thresholds')


valloss = np.empty(0)
for batch_features in val_loader:
        batch_features = batch_features.view(-1, 1, 32, 32).to(device)
        outputs = model(batch_features)
        loss = squareloss(outputs, batch_features)
        valloss = np.append(valloss, loss.detach().cpu().numpy())


malloss = np.empty(0)
for batch_features in mal_val_loader:
        batch_features = batch_features.view(-1, 1, 32, 32).to(device)
        outputs = model(batch_features)
        loss = squareloss(outputs, batch_features)
        malloss = np.append(malloss, loss.detach().cpu().numpy())
# %%

mal_hat = stats.gaussian_kde(malloss)
val_hat = stats.gaussian_kde(valloss)
points = np.linspace(0.01, 0.1, 100)

plt.plot(points, mal_hat(points), label='Malware distribution')
plt.plot(points, val_hat(points), label='Legitimate distribution')
plt.title('Distribution of reconstruction error')
plt.ylim(0, 0.4)
plt.legend()
plt.show()
