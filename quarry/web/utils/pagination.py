class RangeBasedPagination(object):
    """
    Generic range based pagination.
    """
    def __init__(self, queryset, page_key, limit, base_url, referrer_url=None,
                 get_params={}):
        """
        Instantiate RangeBasedPagination.

        Args:
            queryset: A SQLAlchemy queryset.
            page_key: A unique key (string/number) to identify a point
                of reference to paginate from.
            limit: An integer specifying number of items to render
                in a page. A negative value indicates that page
                items are to be fetched before the point of reference,
                and a positive value means that page items are to be
                fetched after the point of reference.
            base_url: A string for the base url of the paginated view.
            referrer_url: A string for url from which the current page
                has been referred.
            get_params: A dictionary for request's GET parameters.
        """
        self.queryset = queryset
        self.page_key = page_key
        self.limit = abs(limit)
        self.direction = 'next' if limit >= 0 else 'prev'
        self.base_url = base_url
        self.referrer_url = referrer_url or ''
        self.get_params = get_params or {}

    def paginate(self):
        """
        Generate data for rendering the current page.

        Returns:
            A tuple: (page_items, prev_link, next_link)
            where
                page_items: A list of items to be rendered in the
                    current page.
                prev_link: A string for the link to previous page, if any,
                    else, None.
                next_link: A string for the link to the next page, if any,
                    else, None.
        """
        self.filter_queryset()
        self.order_queryset()
        self.limit_queryset()
        page_items = self.get_ordered_page_items()
        prev_link, next_link = self.get_pagination_links(page_items)
        return page_items, prev_link, next_link

    def order_queryset(self):
        """
        Order queryset for pagination.
        """
        pass

    def filter_queryset(self):
        """
        Filter queryset for pagination.
        """
        pass

    def limit_queryset(self):
        """
        Limit queryset for pagination.
        """
        self.queryset = self.queryset.limit(self.limit)

    def get_ordered_page_items(self):
        """
        Fetch all items from the resulting queryset, and order
        the list of items in the page, if needed.
        """
        items = self.queryset.all()
        if self.direction == 'prev':
            items.reverse()
        return items

    def get_pagination_links(self, page_items):
        """
        Get pagination links for the current page.

        Args:
            page_items: List of items in the current page.

        Returns:
            A tuple: (prev_link, next_link)
            where:
                prev_link: A string for the link to the previous
                    page, if any, else None.
                next_link: A string for the link to the next
                    page, if any, else None.
        """
        page_items_count = len(page_items)
        prev_link = next_link = None
        if page_items_count == 0 and self.referrer_url.find(
                self.base_url) >= 0:
            if self.direction == 'next':
                prev_link = self.referrer_url
            elif self.direction == 'prev':
                next_link = self.referrer_url
        elif page_items_count <= self.limit:
            if self.page_key and (self.direction == 'next' or (
                    self.direction == 'prev' and
                    page_items_count == self.limit)):

                prev_link = self.get_page_link(
                    page_key=self.get_page_key_from_page_item(page_items[0]),
                    limit=-1 * self.limit)
            if self.direction == 'prev' or (
                    self.direction == 'next' and
                    page_items_count == self.limit):
                next_link = self.get_page_link(
                    page_key=self.get_page_key_from_page_item(page_items[-1]),
                    limit=self.limit)
        return prev_link, next_link

    def get_page_key_from_page_item(self, page_item):
        """
        Get page key for an item in a page.

        Args:
            page_item: An item from the items list to be
                rendered in the current page.

        Returns:
            A key (string/number) to be used as a key to
            identify a page.
        """
        return page_item.id

    def get_page_link(self, page_key, limit):
        """
        Get paginated link for a page.

        Args:
            page_key: A unique key (string/number) to identify a point
                of reference to paginate from.
            limit: An integer specifying number of items to render
                in a page. A negative value indicates that page
                items are to be fetched before the point of reference,
                and a positive value means that page items are to be
                fetched after the point of reference.

        Returns:
            A string for the paginated link.
        """
        return '{url}?from={page_key}&limit={limit}'.format(
            url=self.base_url, page_key=page_key, limit=limit)
