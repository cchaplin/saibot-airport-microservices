import json, arrow
from flask import Blueprint, request
from mongo import CheckInCounter, Flight, Gate, Passenger

bp = Blueprint('flight', __name__, url_prefix='/flight')

@bp.route('/<id>', methods=['GET'])
def get_flight(id):
    """
    get single flight by id
    ---
    parameters:
        -   in: path
            name: id
            required: true
            schema:
                type: string
                format: uuid
                example: 5cdc02bbe3dafee2a3538d8e
            description: ID of the flight

    responses:
        200:
            description: Found a flight
            schema:
                $ref: "#/definitions/Flight"
    """
    flight = Flight.objects.get(id=id)

    return json.dumps(flight.to_parsable()), 200, {'Content-Type': 'application/json'}

@bp.route('', methods=['GET'])
def get_all():
    """
    get all flights
    ---
    responses:
        200:
            description: Flights found
            schema:
                type: array
                items:
                    $ref: "#/definitions/Flight"
    """
    flights = [f.to_parsable() for f in Flight.objects]
    return json.dumps(flights), 200, {'Content-Type': 'application/json'}

@bp.route('/count', methods=['GET'])
def get_count():
    """
    get amount flights
    ---
    responses:
        200:
            schema:
                type: object
                properties:
                    count:
                        type: integer
                        example: 30
    """
    return json.dumps({'count': Flight.objects.count()}), 200, {'Content-Type': 'application/json'}

@bp.route('/schedule/<type>', methods=['GET'])
def getSchedule(type):
    """
    get flights between a time range and filtered by type
    ---
    parameters:
        -   in: path
            name: type
            required: true
            schema:
                type: integer
            example: 1
            description: 'Whether to get incoming or outgoing flights (0 = incoming/arriving, 1 = outgoing/departing)'
        -   in: query
            name: start_date
            schema:
                type: string
                example: '2019-05-15'
            description: Start of range of dates to look for flights (included). Defaults to today
        -   in: query
            name: end_date
            schema:
                type: string
                example: '2019-05-16'
            description: End of range of dates to look for flights (non-included). Defaults to tomorrow
    responses:
        200:
            schema:
                type: object
                properties:
                    start_date:
                        type: string
                        example: today
                        description: Start of range of dates to look for flights (included)
                    end_date:
                        type: string
                        example: tomorrow
                        description: End of range of dates to look for flights (non-included)
                    flights:
                        $ref: '#/definitions/Flight'
    """
    params = request.args

    now = arrow.now().date()
    type = bool(int(type))

    start_date = arrow.get(now)
    end_date = arrow.get(now).shift(days=+1)

    if 'start_date' in params.keys():
        start_date = arrow.get(params['start_date'])

    if 'end_date' in params.keys():
        end_date = arrow.get(params['end_date'])

    flights = [f.to_parsable() for f in Flight.objects(time__gte=start_date.datetime, time__lte=end_date.datetime, type=type)]

    return json.dumps({'start': start_date.format('YYYY-MM-DD'), 'end': end_date.format('YYYY-MM-DD'), 'flights': flights}), 200, {'Content-Type': 'application/json'}

@bp.route('/request', methods=['POST'])
def requestFreeGate():
    """
    request/create a new flight
    ---
    parameters:
        -   in: body
            name: flight
            description: the flight to create
            schema:
                type: object
                properties:
                    nr:
                        type: integer
                        description: Number of the flight
                        example: 102
                    type:
                        type: boolean
                        description: Whether the flight is departing or not
                    location:
                        type: string
                        example: 'Oakland, CA'
                        description: Location where the flight is coming from / going to
                    time:
                        type: string
                        example: 2019-05-15 11:13:00
                        description: Time of actual departure/arrival for the flight
                    airplane:
                        $ref: '#/definitions/Airplane'

    responses:
        200:
            description: newly created flight
            schema:
                $ref: '#/definitions/Flight'
        412:
            description: when there are no more free spots around that time
            schema:
                type: object
                properties:
                    msg:
                        type: string
                        example: 'Sorry no free spots available around this time'
    """
    flight = json.loads(request.data.decode('UTF-8'))

    is_departing = flight['type'] == 1
    time = arrow.get(flight['time'], 'YYYY-MM-DD HH:mm:ss')

    flight['time'] = time.datetime
    flight['type'] = is_departing

    start_time = time.shift(hours=-1) if is_departing else time.shift(minutes=-15)
    end_time = time.shift(minutes=+15) if is_departing else time.shift(hours=+1)

    overlapping_count = Flight.objects(start_time__lte=end_time.datetime, time__gte=start_time.datetime).count()
    gates_count = 20 # needs to be coupled to a database value

    if overlapping_count < gates_count:
        new_flight = Flight(**flight)
        new_flight.save()

        return json.dumps(new_flight.to_parsable()), 200, {'Content-Type': 'application/json'}
    else:
        return json.dumps({'msg': 'Sorry no free spots available around this time'}), 412, {'Content-Type': 'application/json'}

@bp.route('/<id>/set_counter_gate', methods=['POST'])
def set_counter_and_gate(id):
    """
    add a check-in counter and a gate to an existing flight
    ---
    parameters:
        -   in: body
            name: gate & check-in counter
            description: the gate and check-in counter to add to the flight
            schema:
                type: object
                properties:
                    gate:
                        $ref: '#/definitions/Gate'
                    check_in_counter:
                        $ref: '#/definitions/CheckInCounter'
        -   in: path
            name: id
            required: true
            schema:
                type: string
                format: uuid
                example: 5cdc02bbe3dafee2a3538d8e
            description: ID of the flight
    responses:
        200:
            description: updated flight
            schema:
                $ref: '#/definitions/Flight'
    """
    data = json.loads(request.data.decode('UTF-8'))
    counter = CheckInCounter(**data['counter'])
    gate = Gate(**data['gate'])

    flight = Flight.objects.get(id=id)
    flight.update_props({'check_in_counter': counter, 'gate': gate})
    flight.save()

    return json.dumps(flight.to_parsable()), 200, {'Content-Type': 'application/json'}

@bp.route('/<id>/cancel', methods=['POST'])
def cancel_flight(id):
    """
    cancel a flight (soft-delete)
    ---
    parameters:
        -   in: path
            name: id
            required: true
            schema:
                type: string
                format: uuid
                example: 5cdc02bbe3dafee2a3538d8e
            description: ID of the flight
    responses:
        200:
            description: updated (canceled) flight
            schema:
                $ref: '#/definitions/Flight'
    """
    flight = Flight.objects.get(id=id)
    flight.cancel()

    return json.dumps(flight.to_parsable()), 200, {'Content-Type': 'application/json'}

@bp.route('/<id>/add_passenger', methods=['POST'])
def add_passenger(id):
    """
    add passenger(s) to a flight
    ---
    parameters:
        -   in: path
            name: id
            required: true
            schema:
                type: string
                format: uuid
                example: 5cdc02bbe3dafee2a3538d8e
            description: ID of the flight
        -   in: body
            name: passenger(s)
            description: Passenger(s) to add. For multiple, wrap passengers in an array.
            schema:
                $ref: '#/definitions/Passenger'
    responses:
        200:
            description: updated flight
            schema:
                $ref: '#/definitions/Flight'
    """
    flight = Flight.objects.get(id=id)

    passengers = json.loads(request.data.decode('UTF-8'))

    if isinstance(passengers, dict):
        passengers = [passengers]

    for p in passengers:
        flight.passengers.append(Passenger(**p))

    flight.save()

    return json.dumps(flight.to_parsable()), 200, {'Content-Type': 'application/json'}
