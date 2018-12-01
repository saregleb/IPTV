
service_basic = """
[Unit]
Description={service_description}

[Service]
User={user}
Type=simple
ExecStart={script_path}

[Install]
WantedBy=multi-user.target
"""

