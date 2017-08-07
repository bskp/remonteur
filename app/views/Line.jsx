'use babel';

import React, {PropTypes} from 'react';
import update from 'react/lib/update';
import { findDOMNode } from 'react-dom';
import { DragSource, DropTarget } from 'react-dnd';

var sanitizeHtml = require('sanitize-html');

import Color from 'color';

let maleColor = Color().hsl(197, 90, 50);
let femaleColor = Color().hsl(23, 90, 50);

const movies_dir = require('../db').movies_dir;


const lineSource = {
    beginDrag(props, monitor, component) {
        return {
            data: props.data,
            id: props.id,
            index: props.index,
            removeLine: props.removeLine
        };
    }
};

const lineTarget = {
  drop(props, monitor, component) {
    const dragIndex = monitor.getItem().index;
    const hoverIndex = props.index;

    // Don't replace items with themselves
    if (monitor.getItem().id === props.id) {
      return;
    }

    // Determine rectangle on screen
    const hoverBoundingRect = findDOMNode(component).getBoundingClientRect();

    // Get vertical middle
    const hoverMiddleY = (hoverBoundingRect.bottom - hoverBoundingRect.top) / 2;

    // Determine mouse position
    const clientOffset = monitor.getClientOffset();

    // Get pixels to the top
    const hoverClientY = clientOffset.y - hoverBoundingRect.top;

    // Only perform the move when the mouse has crossed half of the items height
    // When dragging downwards, only move when the cursor is below 50%
    // When dragging upwards, only move when the cursor is above 50%

    // Dragging downwards
    if (dragIndex < hoverIndex && hoverClientY < hoverMiddleY -20) {
      return;
    }

    // Dragging upwards
    if (dragIndex > hoverIndex && hoverClientY > hoverMiddleY +20) {
      return;
    }

    // Time to actually perform the action
    //props.moveLine(dragIndex, hoverIndex, monitor.getItem().data);
    monitor.getItem().removeLine(dragIndex);
    props.addLine(hoverIndex, monitor.getItem().data);

    // Note: we're mutating the monitor item here!
    // Generally it's better to avoid mutations,
    // but it's good here for the sake of performance
    // to avoid expensive index searches.
    monitor.getItem().index = hoverIndex;
    monitor.getItem().id = props.id;
  }
};


@DropTarget('line', lineTarget, (connect, monitor) => ({
  connectDropTarget: connect.dropTarget(),
  isOver: monitor.isOver()
}))
@DragSource('line', lineSource, (connect, monitor) => ({
  connectDragSource: connect.dragSource(),
  isDragging: monitor.isDragging()
}))


export default class Line extends React.Component {
    static propTypes = {
        connectDragSource: PropTypes.func.isRequired,
        connectDropTarget: PropTypes.func.isRequired,
        index: PropTypes.number.isRequired,
        isDragging: PropTypes.bool.isRequired,
        id: PropTypes.any.isRequired,
        data: PropTypes.any.isRequired,
        addLine: PropTypes.func.isRequired,
        removeLine: PropTypes.func.isRequired,
    };

    constructor() {
        super();
        this.state = {playing: false};
    }
    handleClick = (e) => {
        this.refs.audio.play();
    }
    handlePlay = (e) => {
        this.setState({playing: true});
    }
    handleEnded = (e) => {
        this.setState({playing: false});
    }
    render() {
        const { data, isDragging, isOver, connectDragSource, connectDropTarget } = this.props;

        let sextimate = Math.min(1, Math.max(0,
            (this.props.data.sextimate - 80)/150
        ));

        //let color = maleColor.mix(femaleColor, sextimate).hslString();
        let color = femaleColor.clone();
        color.mix(maleColor, sextimate);

        let dragging = this.props.draggable & isDragging ? 'dragging' : '';
        let playing = this.state.playing ? 'playing' : '';
        let over = this.props.draggable & isOver ? 'over' : '';

        let s = Math.floor(this.props.data.start);
        let seconds = s % 60;
        let minutes = ((s-seconds)/60)%60;
        let hours = ((s-seconds-minutes*60)/3600)%60;

        let content = {__html: sanitizeHtml(this.props.data.text, {
            allowedTags: [ 'b', 'i', 'em', 'strong' ]
        }) };

        return connectDragSource(connectDropTarget(
            <div    className={`line ${dragging} ${playing} ${over}`}
                    title={this.props.data.title +  " @ " +
                           hours + ":" + minutes + ":" + seconds + "\n" +
                           Math.floor(this.props.data.sextimate) + " Hz, " +
                           Math.ceil(this.props.data.duration) + "s"}
                    onClick={this.handleClick}
                    onPlay={this.handlePlay}
                    onEnded={this.handleEnded}
                >
                <div style={{backgroundColor: color.hslString()}} >
                <span dangerouslySetInnerHTML={content}></span>
                <audio ref="audio" src={movies_dir+'/'+this.props.data.audio}></audio>
                <span   className="cursor"
                        style={{transitionDuration: `${this.props.data.duration}s`}} >
                </span>
                </div>
            </div>
        ));
    }

}
