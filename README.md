This is a fork of NHS Digital's [identity-service-api](https://github.com/NHSDigital/identity-service-api) repo.

We've just made a copy of it so that some folks at NHS Wales can do a bit of poking around :)

Here are a few additions that we've made:

### Dev Containers
 - `.devcontainer/devcontainer.json`
 - `Dockerfile`
 - `.gitattributes`

These files mean you can now spin up a container to use with VS Code's ["Remote - Containers" extension][ms-vscode-remote.remote-containers], giving you an environment with all the dependencies installed and ready to go.

Why do this? Well, to run the makefile commands from the README of the original repo, you'll need to ensure you've installed the right versions of python, poetry, node (and "make" of course).
If you're developing on Windows, you might find that attempting to get that all working just ruins your day! 

[ms-vscode-remote.remote-containers]: https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-containers


### Ansible "jinja2" Templates

- `proxies.template-playbook.yml`

Another thing you might notice is that the files are riddled with {{ PLACEHOLDERS }} for jinja templates. However, there's no explanation of how to process them.

For that, you'll need to decipher the pipeline templates in the `azure` folder, and divine the correct values for the variables... that way madness lies!

Instead, you can spin up the dev container (see above) and run the following command:

```sh
ansible-playbook proxies.template-playbook.yml -i "localhost,"
```

It will process the templates and output them to the `build` folder. If you want to edit the variable values, you can find them in `proxies.template-playbook.yml`.