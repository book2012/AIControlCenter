FROM wordpress:cli@sha256:f8aeb68164c6a04f5dcc91da30d8ffa096b0f7fafb7a65f144c2dd62587caca0

USER root
RUN mkdir -p /opt/aicontrolcenter
COPY cache/woocommerce.zip /opt/aicontrolcenter/woocommerce.zip
ADD --checksum=sha256:163b5bf217dad76a823432d8c01598ab3dc3f15cbdd69067b98f5a6ddf05c1c4 --chmod=0444 https://downloads.wordpress.org/theme/storefront.4.6.2.zip /opt/aicontrolcenter/storefront.zip
COPY bootstrap/bootstrap-commerce.sh /usr/local/bin/bootstrap-commerce
RUN chmod 0444 /opt/aicontrolcenter/woocommerce.zip \
    && chmod 0555 /usr/local/bin/bootstrap-commerce
USER 82

ENTRYPOINT ["/usr/local/bin/bootstrap-commerce"]
CMD []
