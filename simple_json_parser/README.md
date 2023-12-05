# simple json parser

Simple tool used for parsing _json_-style dictionaries / strings into more readable format. It was created for more useful troubleshooting of logger dictionaries and some outputs that are utilising stdin.

## Usage

```
echo '<json_string>' | python script.py <key1> <key2> ... <keyN>
```

## Example

1. Usage with json-style logger message, containing several fields
```
echo '{"level": "info", "message": "This is a log message", "timestamp": "2023-04-01T12:00:00Z"}' | python json_parser.py message timestamp
```

2. Adding as an alias to .bash / .zsh profile, for simplifying its work

    1) Make a script file executable:

    ```
    chmod +x json_parser.py
    ```

    2) (Optional) Copy the script to the `/usr/local/bin` folder, to allow PATH variable execute it without providing a full path:
    
    ```
    sudo cp json_parser.py /usr/local/bin/
    ```

    3) Open a suitable for you text editor, and access a bash/zsh profile file for editing:

    ```
    vim ~/.bashrc
    ```
    
    4) Add an alias parameter, to allow execute the script directly from the terminal:

    ```
    alias jsonparse='json_parser.py'
    ```

    OR, if you have skipped step 2:

    ```
    alias jsonparse='python /<path_to_repository>/simple_json_parser/json_parser.py'
    ```

    5) Save and close the file in text editor.

    6) Source your bash profile to apploy the changes. Or, re-open the terminal window, which will do the same trick:

    ```
    source ~/.bashrc
    ```
