import os
os.environ['THEANO_FLAGS']='device=gpu0'
import matplotlib
import numpy as np
np.random.seed(123)
import matplotlib.pyplot as plt
import lasagne
import theano
import theano.tensor as T
from spatialtransformerlayer import SpatialTransformerLayer

conv = lasagne.layers.Conv2DLayer
pool = lasagne.layers.MaxPool2DLayer
dense = lasagne.layers.DenseLayer
relu = lasagne.nonlinearities.rectify

NUM_EPOCHS = 500
BATCH_SIZE = 256
LEARNING_RATE = 0.001
DIM = 54
NUM_CLASSES = 11
from scipy.io import loadmat

def load_data():
    # data = np.load(mnist_cluttered)
    
    data=loadmat('train_SVHN_multi.mat')
    X_train0 = data['train_SVHN_multi'].transpose()
    
    data=loadmat('test_SVHN_multi.mat')
    X_test = data['test_SVHN_multi'].transpose()

    data=loadmat('train_SVHN_label_multi.mat')
    y_train0 = np.squeeze(data['train_SVHN_label_multi'])
    
    data=loadmat('test_SVHN_label_multi.mat')
    y_test = np.squeeze(data['test_SVHN_label_multi'])
    
    X_train = X_train0[:100000]
    y_train = y_train0[:100000]
    
    X_valid = X_train0[-40000:]
    y_valid = y_train0[-40000:]
    
    # reshape for convolutions
    X_train = X_train.reshape((X_train.shape[0], 3, DIM, DIM)).transpose(0,1,3,2)
    X_valid = X_valid.reshape((X_valid.shape[0], 3, DIM, DIM)).transpose(0,1,3,2)
    X_test = X_test.reshape((X_test.shape[0], 3, DIM, DIM)).transpose(0,1,3,2)
    
    print "Train samples:", X_train.shape
    print "Validation samples:", X_valid.shape
    print "Test samples:", X_test.shape
    
    return dict(
                X_train=lasagne.utils.floatX(X_train),
                y_train=y_train.astype('int32'),
                X_valid=lasagne.utils.floatX(X_valid),
                y_valid=y_valid.astype('int32'),
                X_test=lasagne.utils.floatX(X_test),
                y_test=y_test.astype('int32'),
                num_examples_train=X_train.shape[0],
                num_examples_valid=X_valid.shape[0],
                num_examples_test=X_test.shape[0],
                input_height=X_train.shape[2],
                input_width=X_train.shape[3],
                output_dim=10,)
data = load_data()


plt.figure(figsize=(7,7))
plt.imshow(data['X_train'][101].reshape(3,DIM, DIM).transpose((1,2,0)), cmap='gray', interpolation='none')
plt.title('Cluttered MNIST', fontsize=20)
plt.axis('off')
plt.show()


def build_model(input_width, input_height, output_dim,
                batch_size=BATCH_SIZE):
    ini = lasagne.init.HeUniform()
    l_in = lasagne.layers.InputLayer(shape=(None, 3,  input_width, input_height),)
    
    # Localization network
    b = np.zeros((2, 3), dtype=theano.config.floatX)
    b[0, 0] = 1
    b[1, 1] = 1
    b = b.flatten()
    loc_l1 = pool(l_in, pool_size=(2, 2))
    loc_l2 = conv(loc_l1, num_filters=20, filter_size=(5, 5), W=ini)
    loc_l3 = pool(loc_l2, pool_size=(2, 2))
    loc_l4 = conv(loc_l3, num_filters=20, filter_size=(5, 5), W=ini)
    loc_l5 = dense(loc_l4, num_units=50, W=lasagne.init.HeUniform('relu'))
    loc_out = dense(loc_l5, num_units=6, b=b, W=lasagne.init.Constant(0.0),nonlinearity=lasagne.nonlinearities.identity)

    # Transformer network
    l_trans1 = SpatialTransformerLayer([l_in, loc_out], ds_rate=3.0)
    print "Transformer network output shape: ", l_trans1.output_shape

    # Classification network
    class_l1 = conv(l_trans1,num_filters=48,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l2 = pool(class_l1, pool_size=(2, 2))
    class_l3 = conv(class_l2,num_filters=64,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l4 = conv(class_l3,num_filters=128,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l5 = pool(class_l4, pool_size=(2, 2))
    class_l6 = conv(class_l5,num_filters=160,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l7 = conv(class_l6,num_filters=192,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l8 = pool(class_l7, pool_size=(2, 2))    
    class_l9 = conv(class_l8,num_filters=192,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l10 = conv(class_l9,num_filters=192,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)    
    class_l11 = pool(class_l10, pool_size=(2, 2))    
    class_l12 = conv(class_l11,num_filters=192,filter_size=(5, 5),nonlinearity=relu,W=ini,pad=2)
    class_l13 = dense(class_l12,num_units=256,nonlinearity=relu,W=ini)
    class_l14 = dense(class_l13,num_units=256,nonlinearity=relu,W=ini)
    
    l_out1 = dense(class_l14,num_units=output_dim,nonlinearity=lasagne.nonlinearities.softmax,W=ini)
    l_out2 = dense(class_l14,num_units=output_dim,nonlinearity=lasagne.nonlinearities.softmax,W=ini)
    l_out3 = dense(class_l14,num_units=output_dim,nonlinearity=lasagne.nonlinearities.softmax,W=ini)
    l_out4 = dense(class_l14,num_units=output_dim,nonlinearity=lasagne.nonlinearities.softmax,W=ini)
    l_out5 = dense(class_l14,num_units=output_dim,nonlinearity=lasagne.nonlinearities.softmax,W=ini)

    l_out = lasagne.layers.ConcatLayer((l_out1,l_out2,l_out3,l_out4,l_out5))

    return l_out, l_trans1

model, l_transform = build_model(DIM, DIM, NUM_CLASSES)
model_params = lasagne.layers.get_all_params(model, trainable=True)


X = T.tensor4()
y = T.ivector()

# training output
output_train = lasagne.layers.get_output(model, X, deterministic=False)

# evaluation output. Also includes output of transform for plotting
output_eval, transform_eval = lasagne.layers.get_output([model, l_transform], X, deterministic=True)

sh_lr = theano.shared(lasagne.utils.floatX(LEARNING_RATE))
cost = T.mean(T.nnet.categorical_crossentropy(output_train, y))
updates = lasagne.updates.adam(cost, model_params, learning_rate=sh_lr)

train = theano.function([X, y], [cost, output_train], updates=updates)
eval = theano.function([X], [output_eval, transform_eval])



def train_epoch(X, y):
    num_samples = X.shape[0]
    num_batches = int(np.ceil(num_samples / float(BATCH_SIZE)))
    costs = []
    correct = 0
    for i in range(num_batches):
        idx = range(i*BATCH_SIZE, np.minimum((i+1)*BATCH_SIZE, num_samples))
        X_batch = X[idx]
        y_batch = y[idx]
        cost_batch, output_train = train(X_batch, y_batch)
        costs += [cost_batch]
        preds = np.argmax(output_train, axis=-1)
        correct += np.sum(y_batch == preds)
    
    return np.mean(costs), correct / float(num_samples)


def eval_epoch(X, y):
    output_eval, transform_eval = eval(X)
    preds = np.argmax(output_eval, axis=-1)
    acc = np.mean(preds == y)
    return acc, transform_eval


valid_accs, train_accs, test_accs = [], [], []
try:
    for n in range(NUM_EPOCHS):
        train_cost, train_acc = train_epoch(data['X_train'], data['y_train'])
        valid_acc, valid_trainsform = eval_epoch(data['X_valid'], data['y_valid'])
        test_acc, test_transform = eval_epoch(data['X_test'], data['y_test'])
        valid_accs += [valid_acc]
        test_accs += [test_acc]
        
        if (n+1) % 20 == 0:
            new_lr = sh_lr.get_value() * 0.7
            print "New LR:", new_lr
            sh_lr.set_value(lasagne.utils.floatX(new_lr))
    
        print "Epoch {0}: Train cost {1}, Train acc {2}, val acc {3}, test acc {4}".format(n, train_cost,train_acc, valid_acc, test_acc)
except KeyboardInterrupt:
    pass


plt.figure(figsize=(9,9))
plt.plot(1-np.array(train_accs), label='Training Error')
plt.plot(1-np.array(valid_accs), label='Validation Error')
plt.legend(fontsize=20)
plt.xlabel('Epoch', fontsize=20)
plt.ylabel('Error', fontsize=20)
plt.show()


plt.figure(figsize=(7,14))
for i in range(3):
    plt.subplot(321+i*2)
    plt.imshow(data['X_test'][i].reshape(DIM, DIM), cmap='gray', interpolation='none')
    if i == 0:
        plt.title('Original 60x60', fontsize=20)
    plt.axis('off')
    plt.subplot(322+i*2)
    plt.imshow(test_transform[i].reshape(DIM//3, DIM//3), cmap='gray', interpolation='none')
    if i == 0:
        plt.title('Transformed 20x20', fontsize=20)
    plt.axis('off')
plt.tight_layout()

