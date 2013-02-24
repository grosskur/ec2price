create table availability_zones (
    id uuid not null,
    api_name text not null,
    primary key (id),
    unique (api_name)
);

create table instance_types (
    id uuid not null,
    api_name text not null,
    display_name text not null,
    primary key (id),
    unique (api_name),
    unique (display_name)
);

create table spot_prices (
    id uuid not null,
    availability_zone_id uuid not null,
    instance_type_id uuid not null,
    ts timestamptz not null,
    price decimal not null,
    primary key (id),
    unique (ts, availability_zone_id, instance_type_id),
    foreign key (availability_zone_id) references availability_zones (id),
    foreign key (instance_type_id) references instance_types (id)
);
