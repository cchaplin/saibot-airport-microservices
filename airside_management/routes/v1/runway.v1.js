const express = require('express');
const router = express.Router();
const amqpManager = require('../../events/amqp.manager');
const uuid = require('uuid/v4');

router.get('/', (req, res) => {
	amqpManager.connect()
		.then((channel) => {
			amqpManager.sendMessageToQueue(channel, 'airside-runway', JSON.stringify({
				message: 'Hoi',
				code: 200
			}))
		});
	res.status(200).json({message: 'Welcome to Runway V1 API'});
});

router.post('/', (req, res) => {
	let body = req.body;
	
	//Check for missing properties
	if (!body.side1 || !body.side2 || !body.length || !body.width) {
		res.status(400).json({error: 'Invalid request.'});
	}
	
	//TODO Implement logic to add runway to database
	
	//Create message payload
	let payload = {
		id: uuid(),
		message: 'New runway has been added successfully.',
		from: 'airside_management',
		type: 'CREATE',
		data: {
			side1: body.side1,
			side2: body.side2,
			length: body.length,
			width: body.width
		},
		old_data: {}
	}
	
	//Send message
	amqpManager.connect()
		.then((channel) => {
			amqpManager.sendMessageToQueue(channel, 'airside-runway', JSON.stringify(payload));
			res.status(201).json(payload);
		})
});

router.delete('/{id}', (req, res) => {
	
});

module.exports = router;