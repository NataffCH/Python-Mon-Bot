# MoneroBOT
This Python script is designed to read the Monero (XMR) blockchain from Onion Monero Blockchain Explorer (OMBE) in JSON format and convert its data into a SQL database. Originally developed as an assignment for the Distributed System Security course at HBKU during the spring of 2020.

Usage Guide
-----------

### Running the Monero Blockchain to SQL Converter

1.  Clone the repository to your local machine:
        
    ```
    git clone https://github.com/your-username/monero-blockchain-converter.git](https://github.com/husseinalygit/MoneroBOT.git
    cd MoneroBOT
    ```
    
3.  Execute the script using the following command:
        
    `python monbot.py`
    
4.  Upon the first execution, you will be greeted with the following message:
        
    ```
    Monero Browser version 0.0.1, designed by Hussein Aly.
    Welcome to the Monero BOT! What do you want me to do?
    1- Extract Block metadata to SQLite DB
    999- Exit
    ```
    
5.  To exit the script, choose option 999.
    
6.  If you choose option 1 (Extract Block metadata to SQLite DB), you will be prompted to enter a unique database name:
        
    ```
    You chose option 1, which is Extract Block metadata to SQLite DB
    Please enter the DB name (must be unique) <user_input>
    ```
    
8.  Next, you will be asked to provide starting and ending block IDs. Both must be integers:
        
    ```
    Starting block ID (int only)? <user_input>
    End block ID (int only)? <user_input>
    ```
        
9.  An SQLite database with the provided name will be created in the same path where the script was executed.
    
10. You will then be directed back to the main menu for further actions.

### Database Design

The data obtained from OMBE API calls is in JSON format, requiring mapping to SQL format for effective storage. Notably, certain fields, such as the `extra` field, contain an array of integers with variable length. To address this, a separate table has been created, where each element of the array represents a row entry. These rows are linked to the `Transaction` table through the `transaction_id` field.

Similar treatment is applied to the `vin_txs` and `vout_txs` tables, where the number of inputs and outputs in a single transaction varies, and they are represented as arrays with variable length in the JSON format. The key offsets undergo a similar process as `extra`, `vin_txs`, and `vout_txs`.

**Figure 1: SQL Schema Overview**
![DB Schema](https://github.com/husseinalygit/MoneroBOT/blob/e88de897d0e81418ca5ae648bf6b9faf309aa6ed/db_schema.png)

For a detailed understanding of the fields and relationships, refer to [report.pdf](https://github.com/husseinalygit/MoneroBOT/blob/e88de897d0e81418ca5ae648bf6b9faf309aa6ed/report.pdf)
