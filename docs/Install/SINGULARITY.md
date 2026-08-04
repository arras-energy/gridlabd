
# Running Arras Energy in Singularity on Red Hat

This guide describes how to run the Arras Energy container using Singularity on Red Hat systems, including steps to resolve SSL certificate issues commonly encountered when accessing external resources from within the container.

## Prerequisites

- **Red Hat Linux** (RHEL 7/8 or compatible)
- **Singularity** installed (version 3.x or later recommended)
- Access to the Arras Energy Singularity image (e.g., `python_latest.sif`)
- Sufficient disk quota in your home directory

## Step 1: Copy System Certificate to Home Directory

Singularity containers may not have access to the system SSL certificate bundle by default, causing SSL verification errors when using tools like `curl` or `pip`. To resolve this:

```bash
cp /etc/pki/tls/cert.pem $HOME/cert.pem
```

This copies the system certificate file to your home directory, which is accessible inside the Singularity container.

## Step 2: Launch the Singularity Container

Start a shell inside your Singularity image:

```bash
singularity shell python_latest.sif
```

## Step 3: Set SSL Certificate Environment Variable

Inside the container, set the `SSL_CERT_FILE` environment variable to point to your copied certificate:

```bash
export SSL_CERT_FILE=$HOME/cert.pem
```

This ensures that SSL-enabled tools (e.g., `curl`, `pip`, `requests`) can verify remote servers.

## Step 4: Test SSL Access

Test access to an Arras Energy resource:

```bash
curl -I https://library.arras.energy/US/CA/SLAC/pole_configuration.glm
```

If configured correctly, you should receive an HTTP response header (e.g., `HTTP/2 301`), confirming successful SSL negotiation.

## Example Session

```bash
[username@host ~]$ cp /etc/pki/tls/cert.pem $HOME/cert.pem
[username@host ~]$ singularity shell python_latest.sif
Singularity> export SSL_CERT_FILE=$HOME/cert.pem
Singularity> curl -I https://library.arras.energy/US/CA/SLAC/pole_configuration.glm
HTTP/2 301
content-length: 0
location: http://raw.githubusercontent.com/arras-energy/gridlabd-library/master//US/CA/SLAC/pole_configuration.glm
...
```

## Troubleshooting

- **SSL errors persist:** Double-check the path to the certificate file and that the file is accessible inside the container.
- **Permission denied:** Ensure your home directory and files are readable from within the container.
- **Image not found:** Verify the path and filename of your `.sif` image.

## Additional Notes

- For batch jobs, add `export SSL_CERT_FILE=$HOME/cert.pem` to your job script after launching the container shell or before running any SSL-dependent command.
- If you need additional CA certificates, contact your system administrator.

## References

- [Singularity Documentation](https://sylabs.io/guides/)
- [Arras Energy Documentation](https://arras.energy/)
- [SSL Certificate Issues](https://curl.se/docs/sslcerts.html)
