import os
import time
import requests
import sqlite3

URL = "https://xmrchain.net/api"
transaction_url = 'rawtransaction'
transaction_extra_url = 'transaction'
block_url = 'rawblock'
block_extra_url = 'block'


# sql related code is inspired from https://www.sqlitetutorial.net/sqlite-python

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        return conn
    except Exception as e:
        print(e)
    return conn


def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


def insert_block(conn, block):
    sql = '''INSERT INTO block(hash_id,height, txs_number ,block_size , block_reward , major_version, minor_version, timestamp, prev_id , nounce) VALUES(?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, block)
    conn.commit()
    return cur.lastrowid


def insert_transaction(conn, tx):
    sql = '''INSERT INTO txs(hash_id ,version, unlock,rct_signature_type, txnFee, xmr_inputs, xmr_outputs ,timestamp, coin_base_tx ,block_id ) VALUES(?,?,?,?,?,?,?,?,?,?) '''
    cur = conn.cursor()
    cur.execute(sql, tx)
    conn.commit()
    return cur.lastrowid


def insert_vin_tx(conn, vin):
    sql = '''INSERT INTO vin_txs(amount , key_image, transaction_id) VALUES (?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, vin)
    conn.commit()
    return cur.lastrowid


def insert_vin_key_offset(conn, key_offsets, vin_tx_id):
    sql = '''INSERT INTO key_offsets (vin_tx_id, offset_value) VALUES (?,?)'''
    cur = conn.cursor()
    for offset in key_offsets:
        cur.execute(sql, [vin_tx_id, offset])
    conn.commit()


def insert_vout_tx(conn, vout):
    sql = '''INSERT INTO vout_txs(amount, target_key, transaction_id) VALUES (?,?,?)'''
    cur = conn.cursor()
    cur.execute(sql, vout)
    conn.commit()
    return cur.lastrowid


def insert_extra(conn, extra, tx_id):
    sql = '''INSERT INTO extra(extra_value, transaction_id) VALUES(? , ?)'''
    cur = conn.cursor()
    for value in extra:
        cur.execute(sql, [value, tx_id])
    conn.commit()


def init_db(name):
    # create DB

    conn = create_connection(name)

    sql_create_block_table = """ CREATE TABLE IF NOT EXISTS block (
                                        id integer PRIMARY KEY,
                                        hash_id varchar(64) unique ,
                                        height integer ,
                                        txs_number integer ,
                                        block_size integer, 
                                        block_reward integer,
                                        major_version integer ,
                                        minor_version integer ,
                                        timestamp  timestamp ,
                                        prev_id varchar(64),
                                        nounce integer
                                    ); """

    sql_create_transaction_table = """ CREATE TABLE IF NOT EXISTS txs (
                                        id integer PRIMARY KEY,
                                        hash_id varchar(64) unique,
                                        version integer ,
                                        unlock integer ,
                                        rct_signature_type integer ,
                                        txnFee integer ,
                                        xmr_inputs integer ,
                                        xmr_outputs integer ,
                                        timestamp timestamp ,
                                        coin_base_tx BIT,
                                        block_id integer NOT NULL,
                                        FOREIGN KEY (block_id) REFERENCES block (id)
                                    ); """

    sql_create_vin_txs_table = """ CREATE TABLE IF NOT EXISTS vin_txs(
                                    id integer PRIMARY  KEY , 
                                    amount integer ,
                                    key_image varchar(64),
                                    transaction_id integer NOT NULL ,
                                    FOREIGN KEY (transaction_id) REFERENCES txs (id)
                                );"""

    sql_create_key_offsets = """CREATE TABLE IF NOT EXISTS key_offsets(
                                vin_tx_id integer NOT NULL,
                                offset_value integer,
                                FOREIGN KEY (vin_tx_id) REFERENCES vin_txs (id)
                            );"""

    sql_create_vout_txs_table = """CREATE TABLE IF NOT EXISTS vout_txs(
                                id integer PRIMARY KEY ,
                                amount integer ,
                                target_key varchar(64),
                                transaction_id integer NOT NULL,
                                FOREIGN KEY (transaction_id) REFERENCES txs (id)
                            );"""

    sql_create_extra_table = """CREATE TABLE IF NOT EXISTS extra(
                                id integer PRIMARY KEY,
                                extra_value integer,
                                transaction_id integer NOT NULL,
                                FOREIGN KEY (transaction_id) REFERENCES txs (id)
                            );"""

    # create the tables
    create_table(conn, sql_create_block_table)
    create_table(conn, sql_create_transaction_table)
    create_table(conn, sql_create_vin_txs_table)
    create_table(conn, sql_create_key_offsets)
    create_table(conn, sql_create_vout_txs_table)
    create_table(conn, sql_create_extra_table)

    return conn


def process_block(conn, block_height):
    try:
        # reads a block from monero network and then insert it in sqllie database
        # takes db connection , and block height as a param
        # block_id = '9ef6bb8f9b8bd253fc6390e5c2cdc45c8ee99fad16447437108bf301fe6bd6e1'  # the height of the block
        block_id = block_height
        # get block data
        r = requests.get(url="{}/{}/{}".format(URL, block_url, block_id))
        block = r.json()
        # get extra block data
        r = requests.get(url="{}/{}/{}".format(URL, block_extra_url, block_id))
        block_extra = r.json()
        block_hash = block_extra['data']['hash']
        block_size = block_extra['data']['size']
        block_reward = block_extra['data']['txs'][0]['xmr_outputs']
        coin_base_tx_hash = block_extra['data']['txs'][0]['tx_hash']

        # query transaction information
        transactions_hashes = block['data']['tx_hashes']
        transactions_metadata = []
        transactions_extra = []

        for transaction_hash in transactions_hashes:
            print('querying transaction {}'.format(transaction_hash))

            r = requests.get(url="{}/{}/{}".format(URL, transaction_url, transaction_hash))
            transaction = r.json()
            r = requests.get(url="{}/{}/{}".format(URL, transaction_extra_url, transaction_hash))
            tx_extra = r.json()
            transactions_metadata.append(transaction['data'])
            transactions_extra.append(tx_extra['data'])

        # insert_block
        sql_block = (
            block_hash, block['data']['miner_tx']['vin'][0]['gen']['height'], len(transactions_hashes), block_size,
            block_reward, block['data']['major_version'],
            block['data']['minor_version'], block['data']['timestamp'],
            block['data']['prev_id'], block['data']['nonce'])
        sql_block_id = insert_block(conn, sql_block)

        # insert_coin_base_tx
        coin_base_tx = (
            coin_base_tx_hash, block['data']['miner_tx']['version'],
            block['data']['miner_tx']['unlock_time'],
            block_extra['data']['txs'][0]['rct_type'], block_extra['data']['txs'][0]['tx_fee'],
            block_extra['data']['txs'][0]['xmr_inputs'], block_extra['data']['txs'][0]['xmr_outputs'],
            block['data']['timestamp'],
            int(block_extra['data']['txs'][0]['coinbase']),
            sql_block_id)
        sql_cb_tx_id = insert_transaction(conn, coin_base_tx)

        # insert coin base vout tx
        for vout_meta in block['data']['miner_tx']['vout']:
            coin_base_vout_tx = (
                vout_meta['amount'], vout_meta['target']['tagged_key']['key'],
                sql_cb_tx_id)
            insert_vout_tx(conn, coin_base_vout_tx)

        # insert coinbase extra tx
        insert_extra(conn, block['data']['miner_tx']['extra'], sql_cb_tx_id)

        # insert transactions
        for i, tx_meta in enumerate(transactions_metadata):
            print('processing transaction {}'.format(transactions_hashes[i]))
            tx = (
                transactions_hashes[i], tx_meta['version'], tx_meta['unlock_time'],
                transactions_extra[i]['rct_type'], transactions_extra[i]['tx_fee'],
                transactions_extra[i]['xmr_inputs'], transactions_extra[i]['xmr_outputs'],
                transactions_extra[i]['timestamp'],
                int(transactions_extra[i]['coinbase']), sql_block_id)
            sql_tx_id = insert_transaction(conn, tx)
            for vin_meta in tx_meta['vin']:
                # insert vin_tx
                vin_tx = (
                    vin_meta['key']['amount'], vin_meta['key']['k_image'],
                    sql_tx_id)
                key_offsets = vin_meta['key']['key_offsets']
                sql_vin_tx_id = insert_vin_tx(conn, vin_tx)
                insert_vin_key_offset(conn, key_offsets, sql_vin_tx_id)

            # insert vout tx
            for vout_meta in tx_meta['vout']:
                vout_tx = (
                    vout_meta['amount'], vout_meta['target']['tagged_key']['key'],
                    sql_tx_id)
                sql_vout_id = insert_vout_tx(conn, vout_tx)
            # insert  extra field
            insert_extra(conn, tx_meta['extra'], sql_tx_id)
    except Exception as e:
        print('problem with block {}'.format(block_height))
        print(e)


def extract_block_data_to_sqlite_DB():
    while True:
        db_name = input('Please enter the DB name (must be unique)')
        if os.path.exists(db_name):
            print('DB name already exists, please choose a different name')
            continue
        try:
            conn = init_db(db_name)
            lower_block_lim = int(input('starting block id (int only)?'))
            higher_block_lim = int(input('end block id (int only)?'))
            start_time = time.time()
            for i in range(higher_block_lim - lower_block_lim + 1):
                block_id = i + lower_block_lim
                print('processing block {}'.format(block_id))
                process_block(conn, block_id)
            print('Done, took {:.2f} minutes'.format((time.time() - start_time) / 60))
            break
        except Exception as e:
            print(e)
            continue


if __name__ == '__main__':
    welcome_message = "Monero Browser version 0.0.1, designed by Hussein Aly.\nWelcome to the Monero BOT!\n"
    print(welcome_message)
    exit_choice = 999
    while True:
        content = "What do you want me to do?\n"
        options = {
            1: "Extract Block metadata to SQLite DB",
            exit_choice: "Exit"
        }
        co_routine = {
            1: extract_block_data_to_sqlite_DB,
        }

        for key, val in options.items():  # print the options list
            content += "{}- {}\n".format(key, val)
        print(content)
        try:
            user_choice = int(input())
        except Exception as e:
            print("Wrong Input!")
            continue
        if user_choice == exit_choice:
            exit()

        if user_choice not in options:
            print("Error you entered wrong Choice")
            continue
        print("you choose option {}, which is {}".format(user_choice, options[user_choice]))
        co_routine[user_choice]()
