from __future__ import print_function
from keras.preprocessing import sequence
from keras.models import Sequential,Model
from keras.layers import Dense, Embedding,Convolution1D,Input,Multiply
from keras.callbacks import ModelCheckpoint
from keras.preprocessing.text import  Tokenizer
from nested_lstm import NestedLSTM
import  keras
from ind_rnn import IndRNN
from self_attention_keras import Attention,Position_Embedding

num_classes=10
max_features = 80000
maxlen = 2000  # cut texts after this number of words (among top max_features most common words)
batch_size = 256

def predataset(file):
    train=[]
    label=[]
    max_len=0
    with open(file,encoding="utf8") as file:
        for line in file:
            temp=line.split("\t\t")
            train.append(temp[3])
            label.append(int(temp[2])-1)
            if max_len<len(temp[3]):
                max_len=len(temp[3])
    print("max",max_len)
    return  train ,label


#训练数据预处理
x_train,y_train=predataset("../data/IMDB/train.txt")

# 对句子进行序列映射
tokenizer = Tokenizer()
tokenizer.fit_on_texts(x_train)
x_train = tokenizer.texts_to_sequences(x_train)
y_train = keras.utils.to_categorical(y_train,num_classes=10)
embed_size=len(tokenizer.word_index)
#训练数据预处理
x_test,y_test=predataset("../data/IMDB/test.txt")
# 分词并对句子进行序列映射
x_test = tokenizer.texts_to_sequences(x_test)
y_test = keras.utils.to_categorical(y_test,num_classes=10)


#测试数据预处理
x_val,y_val=predataset("../data/IMDB/dev.txt")
# 分词并对句子进行序列映射
x_val = tokenizer.texts_to_sequences(x_val)
y_val = keras.utils.to_categorical(y_val,num_classes=10)

print('Pad sequences (samples x time)')

x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = sequence.pad_sequences(x_test, maxlen=maxlen)
x_val = sequence.pad_sequences(x_val, maxlen=maxlen)
print('x_train shape:', x_train.shape)
print('x_test shape:', x_test.shape)
print('x_val shape:', x_val.shape)

# configuration matches 4.47 Million parameters with `units=600` and `64 embedding dim`
print('Build model...')

inputs=Input(shape=(maxlen,))
embed=Embedding(embed_size+1, 128, input_shape=(maxlen,))(inputs)
#embed=Position_Embedding()(embed)
Q_Seq=Attention(2,4)([embed,embed,embed])
first_ind=IndRNN(128, recurrent_clip_min=-1, recurrent_clip_max=-1, dropout=0.0, recurrent_dropout=0.0,
                  return_sequences=True)(Q_Seq)
second_ind=IndRNN(128, recurrent_clip_min=-1, recurrent_clip_max=-1, dropout=0.0, recurrent_dropout=0.0,
                  return_sequences=False)(first_ind)

output=Dense(10, activation='softmax')(second_ind)
model=Model(input=[inputs],output=output)
# try using different optimizers and different optimizer configs
model.compile(loss='categorical_crossentropy',
              optimizer='adam',
              metrics=['accuracy'])

model.summary()

print('Train...')
model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=3,
          validation_data=(x_val, y_val),
          callbacks=[ModelCheckpoint('weights/self_imdb_nlstm.h5', monitor='val_acc',
                                     save_best_only=True, save_weights_only=False)])

model.load_weights('weights/self_imdb_nlstm.h5')

score, acc = model.evaluate(x_test, y_test,batch_size = batch_size)
print('Test score:', score)
print('Test accuracy:', acc)
